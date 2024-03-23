import curses
import curses.textpad
import os


# return a list of each line that the file contains
def read_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Split lines longer than MAX_CHARS_PER_LINE characters without splitting words
    split_lines = []
    for line in lines:
        words = line.split(' ')
        temp_line = ''
        for word in words:
            if len(temp_line) + len(word) + 1 > MAX_CHARS_PER_LINE:  # +1 for the space
                split_lines.append(temp_line.strip())
                temp_line = word
            else:
                temp_line += ' ' + word
        split_lines.append(temp_line.strip())

    return split_lines

# i might as well just have sorted the list but why not (breaks if folder name does not contain any digit omegalul)
def cleanName(folderName):
    cleanedName = ""
    for c in folderName:
        if c.isdigit():
            cleanedName += c
    return int(cleanedName)


class Screen(object):
    UP = -1
    DOWN = 1
    
    # initializes the window
    def __init__(self, items, curFileIndex, fileList):
        self.window = None
        self.width = 0
        self.height = 0

        self.init_curses()

        self.items = items # file content
        self.curFileIndex = 0 # index of file in fileList
        self.fileList = fileList # list of filepaths that hold content
        self.amountFiles = len(fileList)

        self.max_lines = MAX_LINES
        self.top = 0
        self.bottom = len(self.items)
        self.current = 0
        self.page = self.bottom // self.max_lines


    def init_curses(self):
        self.window = curses.initscr()
        self.window.keypad(True)

        curses.noecho()
        curses.cbreak()

        curses.start_color()
        curses.init_pair(1, TEXT_COLOR, BG_COLOR)
        curses.init_pair(2, BG_COLOR, TEXT_COLOR)

        self.current = curses.color_pair(2)

        self.height, self.width = self.window.getmaxyx()


    def run(self):
        try:
            self.input_stream()
        except KeyboardInterrupt:
            pass
        finally:
            curses.endwin()


    def input_stream(self):
        while True:
            # keep track of terminal size changes and update if necessary
            global MAX_CHARS_PER_LINE
            global MAX_LINES
            if (MAX_CHARS_PER_LINE != os.get_terminal_size()[0] - 1) or (MAX_LINES != os.get_terminal_size()[1] - 1):
                # update global values
                MAX_CHARS_PER_LINE = os.get_terminal_size()[0] - 1
                MAX_LINES = os.get_terminal_size()[1] - 1
                
                self.max_lines = MAX_LINES
                # re-read the current file from filesystem with new value for MAX_CHARS_PER_LINE
                fileContent = read_file(self.fileList[self.curFileIndex])
                fileNumberInfo = "File " + str(self.curFileIndex+1) + " / " + str(self.amountFiles) + "\n"
                fileContent.insert(0, fileNumberInfo)
                self.items = fileContent
                # recreate window
                self.window.clear()
                self.window.refresh()

            self.display()

            key = self.window.getch()
            if key == curses.KEY_UP:
                self.scroll(self.UP)
            elif key == curses.KEY_DOWN:
                self.scroll(self.DOWN)
            elif key == curses.KEY_LEFT:
                if self.curFileIndex > 0:
                    self.curFileIndex -= 1
                    fileContent = read_file(self.fileList[self.curFileIndex])

                    # add first line to list that shows e.g. "File 1 / 10"
                    fileNumberInfo = "File " + str(self.curFileIndex+1) + " / " + str(self.amountFiles) + "\n"
                    fileContent.insert(0, fileNumberInfo)
                    self.items =  fileContent
                    
                    # reset current line to top of file
                    self.bottom = len(self.items)
                    self.current = 0
                    self.top = 0
                    self.page = self.bottom // self.max_lines

            elif key == curses.KEY_RIGHT:
                if self.curFileIndex < self.amountFiles-1:
                    self.curFileIndex += 1
                    fileContent = read_file(self.fileList[self.curFileIndex])

                    # add first line to list that shows e.g. "File 1 / 10"
                    fileNumberInfo = "File " + str(self.curFileIndex+1) + " / " + str(self.amountFiles) + "\n"
                    fileContent.insert(0, fileNumberInfo)
                    self.items =  fileContent
             
                    # reset current line to top of file
                    self.bottom = len(self.items)
                    self.current = 0
                    self.top = 0
                    self.page = self.bottom // self.max_lines

            elif key == curses.ascii.ESC or key == ord('q'):
                break


    def scroll(self, direction):
        next_line = self.current + direction

        if (direction == self.UP) and (self.top > 0 and self.current == 0):
            self.top += direction
            return

        if (direction == self.DOWN) and (next_line == self.max_lines) and (self.top + self.max_lines < self.bottom):
            self.top += direction
            return

        if (direction == self.UP) and (self.top > 0 or self.current > 0):
            self.current = next_line
            return

        if (direction == self.DOWN) and (next_line < self.max_lines) and (self.top + next_line < self.bottom):
            self.current = next_line
            return


    def paging(self, direction):
        current_page = (self.top + self.current) // self.max_lines
        next_page = current_page + direction

        if next_page == self.page:
            self.current = min(self.current, self.bottom % self.max_lines - 1)

        if (direction == self.UP) and (current_page > 0):
            self.top = max(0, self.top - self.max_lines)
            return

        if (direction == self.DOWN) and (current_page < self.page):
            self.top += self.max_lines
            return


    def display(self):
        self.window.erase()
        for idx, item in enumerate(self.items[self.top:self.top + self.max_lines]):
            if idx == self.current:
                self.window.addstr(idx, 0, item, curses.color_pair(2))
            else:
                self.window.addstr(idx, 0, item, curses.color_pair(1))
        
        self.window.refresh()


def main():
    # Path to text folder root
    PATH_ROOT = "/home/pi/Documents/textfiles"

    # Get list of folders
    folderList = [name for name in os.listdir(PATH_ROOT) if os.path.isdir(os.path.join(PATH_ROOT, name))]
    
    # Determine newest folder (assuming folder names are e.g. 2024-03-20)
    newestFolderValue = 0
    newestFolder = ""
    for folderName in folderList:
        # Remove non-numbers from name to get value that can be compared
        cleanedNameInt = cleanName(folderName)
        # If this value is largest so far remember it and update newestFolder
        if cleanedNameInt > newestFolderValue:
            newestFolder = folderName
            newestFolderValue = cleanedNameInt
    # Update newestFolder to hold full filepath
    newestFolder = PATH_ROOT + "/" + newestFolder + "/txt/"

    # Get list of full filepaths of files in folder
    fileList = [os.path.join(newestFolder, name) for name in os.listdir(newestFolder) if os.path.isfile(os.path.join(newestFolder, name))]
    # Sort filenames acending
    fileList.sort()
    # Remember amount of files
    amountFiles = len(fileList)    
    
    # Read first file (will instantly be shown)
    fileContent = read_file(fileList[0])
    # add first line that shows file x / y
    fileNumberInfo = "File 1" + " / " + str(amountFiles) + "\n"
    fileContent.insert(0, fileNumberInfo)
    
    items = fileContent
    
    screen = Screen(items, 0, fileList)
    screen.run()



TEXT_COLOR = curses.COLOR_WHITE
BG_COLOR = curses.COLOR_BLACK
MAX_CHARS_PER_LINE = os.get_terminal_size()[0] - 1 # if you dont subtract one it will crash after scrolling a bit
MAX_LINES = os.get_terminal_size()[1] - 1
main()

# USAGE: python3 read_v3.py

# ASSUMPTIONS:
# 1. "/home/pi/Documents/textfiles" is a directory that contains folders labelled as "2024-03-20", "2024-03-21", etc.
# 2. Each of these subfolders contains a folder called "txt"
# 3. In the txt folder there are many .txt files that have content you want to read

# WHAT DOES THIS TOOL DO:
# It automatically determines the newest folder by date (e.g. 2024-03-23) and then allows you to read the files it contains. You can ssh to your rpi and navigate through these files using the arrow keys (left = show previous, right = show next, up = pull up tcas, down = scroll down avoid stall)
