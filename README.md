# File Manager

## Description
This program is a simple file manager built using the `curses` library in Python. It provides a text-based interface for navigating, viewing, and managing files and directories. The program supports various operations such as opening files, moving, copying, renaming, deleting, creating directories, touching files, yanking paths, pasting files, and zipping directories.

## Features
- **Navigation**: Use arrow keys to navigate through files and directories.
- **Open Files**: Press `o` or `Enter` to open files with appropriate applications.
- **Move Files**: Press `m` to move files or directories.
- **Copy Files**: Press `c` to copy files or directories.
- **Rename Files**: Press `r` to rename files or directories.
- **Create Directories**: Press `d` to create new directories.
- **Delete Files/Dirs**: Press `x` to delete files or directories.
- **Touch Files**: Press `t` to create new empty files.
- **Yank Paths**: Press `y` to yank (copy the path) of the selected file.
- **Paste Files**: Press `p` to paste yanked files by copying or moving them to the current directory.
- **Zip Directories**: Press `z` to zip the selected directory using `7z`.
- **Quit**: Press `q` to quit the program.

## Installation

### Prerequisites
- Python 3.8 or higher
- Required libraries: `curses`, `os`, `shutil`, `subprocess`, `time`, `glob`, `textwrap`
- External tools: `nvim`, `evince`, `7z` (for opening specific file types and zipping directories)

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/cottnich/FManage.git
   cd FManage

2. Ensure you have the required external tools installed. You can install them using your package manager: 
   ```bash
   sudo apt-get install neovim evince p7zip-full
