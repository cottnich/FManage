import curses
import os
import shutil
import subprocess
import time
import subprocess
import glob
import textwrap

class FileManager:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.current_dir = os.getcwd()
        self.selected = 0  # Track selected file or directory
        self.scroll_offset = 0
        self.files = []

    def list_dir(self):
        """ List files and directories in the current directory """
        self.files = os.listdir(self.current_dir)

    def draw(self):
        """ Draw the file list with scrolling, key bindings, and last modified dates in columns """
        self.stdscr.clear()
        self.list_dir()  # Update the file list for the current directory
        h, w = self.stdscr.getmaxyx()  # Get current screen dimensions

        # Display current directory path
        self.stdscr.addstr(0, 0, f"Current Directory: {self.current_dir}", curses.A_BOLD)

        # Add ".." for navigating up to the parent directory, if not in root
        if self.current_dir != "/":
            self.files = [".."] + self.files

        # Sort the file list alphabetically with files starting with '.' appearing last except for '../'
        self.files.sort(key=lambda x: (x != "..", x.startswith('.'), x.lower()))

        # Column headers: "Name" and "Date Modified"
        name_col_width = max(len("Name"), len(max(self.files, key=len)))
        header = f"{'Name':<{name_col_width}}   {'Date Modified':<25}"
        self.stdscr.addstr(1, 0, header[:w])  # Truncate to screen width if needed

        # Calculate available lines for files by subtracting space for header and keybindings
        max_file_lines = h - 5  # Subtract 2 for header, 2 for keybindings space, and 1 extra

        # Calculate the display range based on scroll_offset
        display_files = self.files[self.scroll_offset:self.scroll_offset + max_file_lines]

        # Display files and directories
        for i, filename in enumerate(display_files):
            full_path = os.path.join(self.current_dir, filename)
            display_name = f"{filename}/" if os.path.isdir(full_path) else filename

            # Attempt to get the last modified time; handle missing or inaccessible files
            try:
                mod_time = time.ctime(os.path.getmtime(full_path))  # Human-readable format
            except (FileNotFoundError, OSError):
                mod_time = "N/A"

            # Truncate display_name and mod_time if they exceed the column width
            truncated_name = display_name[:name_col_width]
            truncated_date = mod_time[:25]

            # Format the row and ensure it fits within the screen width
            row = f"{truncated_name:<{name_col_width}}   {truncated_date}"
            
            # Highlight the selected line, considering the offset
            if self.selected == self.scroll_offset + i:
                self.stdscr.attron(curses.A_REVERSE)
                self.stdscr.addstr(i + 2, 0, row[:w])  # Apply selection to truncated row
                self.stdscr.attroff(curses.A_REVERSE)
            else:
                self.stdscr.addstr(i + 2, 0, row[:w])  # Offset by 2 for header

        # Show keybindings at the bottom
        self.show_keybinds()

        self.stdscr.refresh()

    def show_keybinds(self):
        """ Display key bindings at the bottom of the screen """
        keybinds = "Keybinds: q = Quit | ↑↓ = Navigate | o/Enter = Open | m = Move | c = Copy | r = Rename | d = Mkdir | x = Delete | t = Touch | y = Yank | p = Paste | z = Zip"
        
        # Get the current terminal height and width
        h, w = self.stdscr.getmaxyx()

        # Use textwrap to split the keybinds string into lines that fit within the terminal width
        wrapped_keybinds = textwrap.fill(keybinds, width=w-1)  # Reserve space for margin

        # Display each line of the wrapped keybindings, ensuring they fit within the terminal height
        keybind_lines = wrapped_keybinds.split('\n')

        for i, line in enumerate(keybind_lines):
            if i < h - 1:  # Prevent trying to display past the last line
                self.stdscr.addstr(h - len(keybind_lines) + i, 0, line)
        
        self.stdscr.clrtoeol()  # Clear the rest of the line after the keybinds

    def zip_directory(self):
        """ Zip the selected directory using 7z """
        selected_item = self.files[self.selected]
        full_path = os.path.join(self.current_dir, selected_item)

        if os.path.isdir(full_path):
            # Construct the zip file name (same name as the directory)
            zip_file = f"{full_path}.zip"

            try:
                subprocess.run(["7z", "a", zip_file, full_path], check=True)
                self.stdscr.addstr(curses.LINES - 2, 0, f"Successfully zipped: {zip_file}")
            except subprocess.CalledProcessError:
                self.stdscr.addstr(curses.LINES - 2, 0, "Error zipping directory.")
        else:
            self.stdscr.addstr(curses.LINES - 2, 0, "Selected item is not a directory.")
        
        self.stdscr.refresh()

    def touch(self):
        """ Create a new empty file (like 'touch' command) """
        new_file = self.prompt_user("Enter file name: ")
        try:
            with open(os.path.join(self.current_dir, new_file), 'w') as f:
                pass  # Create an empty file
            self.show_message(f"File {new_file} created successfully.")
        except Exception as e:
            self.show_message(f"Error creating file: {e}")

    def yank(self):
        """ Yank (copy the path) of the selected file """
        selected_file = self.files[self.selected]
        self.clipboard = os.path.join(self.current_dir, selected_file)
        self.show_message(f"Yanked: {self.clipboard}")

    def paste(self):
        """ Paste the yanked file by copying or moving it to the current directory """
        if self.clipboard is None:
            self.show_message("No file yanked. Use 'y' to yank a file first.")
            return

        # Ask for the action: move or copy
        action = self.prompt_user("Move or copy (m/c)? ").strip().lower()
        if action == 'm':
            try:
                destination = os.path.join(self.current_dir, os.path.basename(self.clipboard))
                shutil.move(self.clipboard, destination)
                self.show_message(f"Moved: {os.path.basename(self.clipboard)}")
            except Exception as e:
                self.show_message(f"Error moving file: {e}")
        elif action == 'c':
            try:
                destination = os.path.join(self.current_dir, os.path.basename(self.clipboard))
                shutil.copy(self.clipboard, destination)
                self.show_message(f"Copied: {os.path.basename(self.clipboard)}")
            except Exception as e:
                self.show_message(f"Error copying file: {e}")
        else:
            self.show_message("Invalid option. Please choose 'm' or 'c'.")



    def navigate(self, key):
        """ Handle navigation with scrolling """
        h, _ = self.stdscr.getmaxyx()
        if key == curses.KEY_DOWN and self.selected < len(self.files) - 1:
            self.selected += 1
            if self.selected >= self.scroll_offset + h - 5:
                self.scroll_offset += 1  # Scroll down

        elif key == curses.KEY_UP and self.selected > 0:
            self.selected -= 1
            if self.selected < self.scroll_offset:
                self.scroll_offset -= 1  # Scroll up

    def open_selected(self):
        """ Open a directory or file """
        selected_name = self.files[self.selected]
        selected_path = os.path.join(self.current_dir, selected_name)

        # Navigate upwards if '..' is selected, otherwise go into directory or open file
        if selected_name == "..":
            self.current_dir = os.path.dirname(self.current_dir)  # Go to parent directory
            self.selected = 0
            self.scroll_offset = 0  # Reset scroll position when navigating
        elif selected_name == ".":
            return  # Do nothing if '.' (current directory) is selected
        elif os.path.isdir(selected_path):
            self.current_dir = selected_path  # Change to selected directory
            self.selected = 0
            self.scroll_offset = 0  # Reset scroll position when navigating
        else:
            self.open_file(selected_path)  # Placeholder for opening files

    def open_file(self, path):
        """Open specific file types with corresponding applications or a user-defined application."""
        try:
            # Open common file types directly with corresponding applications
            if path.endswith((".txt", ".md", ".py", ".tex")):  # Text-like files to open in Vim
                curses.endwin()  # Temporarily exit curses to view the editor
                subprocess.run(["nvim", path])
                curses.doupdate()  # Re-enter curses mode
            elif path.endswith(".pdf"):
                curses.endwin()
                subprocess.run(["evince", path])
                curses.doupdate()
            elif path.endswith((".zip", ".7z")):
                curses.endwin()
                subprocess.run(["7z", "e", path])
                curses.doupdate()
            else:
                # Generic file: prompt the user to choose how to open it
                choice = self.prompt_user("Open with (vim/evince/7z/other): ").strip().lower()
                
                if choice == "vim":
                    curses.endwin()
                    subprocess.run(["nvim", path])
                    curses.doupdate()
                elif choice == "evince":
                    curses.endwin()
                    subprocess.run(["evince", path])
                    curses.doupdate()
                elif choice == "7z":
                    curses.endwin()
                    subprocess.run(["7z", "e", path])
                    curses.doupdate()
                elif choice == "other":
                    # Use dmenu to select a program from PATH
                    # Get a list of executable programs in PATH
                    programs = subprocess.check_output("compgen -c", shell=True, universal_newlines=True).splitlines()

                    # Pipe the program list to dmenu for user selection
                    selected_program = subprocess.check_output(
                        "echo '{}' | dmenu -i -p 'Select program'".format("\n".join(programs)),
                        shell=True,
                        universal_newlines=True
                    ).strip()

                    if selected_program:  # If a program is selected
                        try:
                            curses.endwin()
                            subprocess.run([selected_program, path])  # Open file with the selected program
                            curses.doupdate()
                        except FileNotFoundError:
                            self.show_message(f"Error: '{selected_program}' not found.")
                    else:
                        self.show_message("No program selected.")
                else:
                    self.show_message("Unknown command. Please try again.")
        except Exception as e:
            self.show_message(f"Error opening file: {e}")
        finally:
            # Redraw the interface after exiting the application
            self.stdscr.refresh()
            self.draw()

    def move(self, src, dst):
        """ Move a file or directory to a new location """
        try:
            shutil.move(src, dst)
        except Exception as e:
            self.show_message(f"Error moving: {e}")

    def copy(self, src, dst):
        """ Copy a file or directory """
        try:
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy(src, dst)
        except Exception as e:
            self.show_message(f"Error copying: {e}")

    def rename(self, src, dst):
        """ Rename a file or directory """
        try:
            os.rename(src, dst)
        except Exception as e:
            self.show_message(f"Error renaming: {e}")

    def mkdir(self, name):
        """ Create a new directory """
        try:
            os.makedirs(name)
        except Exception as e:
            self.show_message(f"Error creating directory: {e}")

    def remove(self, path):
        """ Remove a file or directory """
        try:
            if os.path.isdir(path):
                os.rmdir(path)  # Remove empty directories
            else:
                os.remove(path)  # Remove files
        except Exception as e:
            self.show_message(f"Error removing: {e}")

    def show_message(self, message):
        """ Show a message at the bottom of the screen """
        self.stdscr.addstr(curses.LINES - 1, 0, message)
        self.stdscr.clrtoeol()
        self.stdscr.refresh()
        self.stdscr.getch()  # Wait for key press to continue
    
    def get_tab_complete(self, input_str):
        """ Return the tab-completed path based on user input """
        matching_files = glob.glob(os.path.join(self.current_dir, input_str) + "*")
        
        if len(matching_files) == 1:
            return matching_files[0]  # Return single match as a string
        elif len(matching_files) > 1:
            # If there are multiple matches, return the first one or handle as needed
            return matching_files[0]  # You could choose to display a list instead
        return input_str

    def prompt_user(self, prompt):
        """ Prompt the user for input with tab completion """
        curses.echo()  # Enable typing in the terminal
        input_str = ""
        while True:
            self.stdscr.addstr(curses.LINES - 2, 0, prompt + input_str)
            self.stdscr.clrtoeol()
            key = self.stdscr.getch()

            if key == ord('\n'):  # Enter key pressed
                break
            elif key == 9:  # Tab key pressed
                input_str = self.get_tab_complete(input_str)
            elif key == 263:  # Backspace key pressed
                input_str = input_str[:-1]
            else:
                input_str += chr(key)  # Add the typed character

        curses.noecho()
        return input_str

def main(stdscr):
    fm = FileManager(stdscr)
    curses.curs_set(0)  # Hide the cursor

    while True:
        fm.draw()
        key = stdscr.getch()

        if key == ord('q'):

            print(fm.current_dir)
            
            break  # Quit
        elif key in (curses.KEY_DOWN, curses.KEY_UP):
            fm.navigate(key)
        elif key == ord('o') or key == 10:  # 'o' or Enter to open selected item
            fm.open_selected()
        elif key == ord('m'):  # Move
            src = os.path.join(fm.current_dir, fm.files[fm.selected])
            dst = os.path.join(fm.current_dir, fm.prompt_user("Move to: "))
            fm.move(src, dst)
        elif key == ord('c'):  # Copy
            src = os.path.join(fm.current_dir, fm.files[fm.selected])
            dst = os.path.join(fm.current_dir, fm.prompt_user("Copy to: "))
            fm.copy(src, dst)
        elif key == ord('r'):  # Rename
            src = os.path.join(fm.current_dir, fm.files[fm.selected])
            dst = os.path.join(fm.current_dir, fm.prompt_user("Rename to: "))
            fm.rename(src, dst)
        elif key == ord('d'):  # Make Directory
            name = os.path.join(fm.current_dir, fm.prompt_user("Directory name: "))
            fm.mkdir(name)
        elif key == ord('x'):  # Remove (delete)
            selected_file = os.path.join(fm.current_dir, fm.files[fm.selected])
            confirmation = fm.prompt_user(f"Are you sure you want to delete {selected_file}? (y/n): ")
            if confirmation.lower() == 'y':
                fm.remove(selected_file)  # Delete file or directory
        elif key == ord('t'):  # Touch
            fm.touch()
        elif key == ord('y'):  # Yank
            fm.yank()
        elif key == ord('p'):  # Paste
            fm.paste()
        elif key == ord('z'):  # Zip
            fm.zip_directory()

# Initialize the curses application
curses.wrapper(main)

