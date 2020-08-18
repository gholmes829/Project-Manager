"""
Author: Grant Holmes
Contact: g.holmes429@gmail.com
Date: Early Summer 2020

Runs program

Classes:
    Driver
"""

from core import settings

import subprocess  # to open terminal in background to execute commands to
from datetime import date  # for top of main.cpp


class Driver:
    """organizes and runs code"""
    def __init__(self):
        self.running = True
        self.allProjectsFiles = None

    def run(self):
        """gets user input and responds with appropriate function"""
        while self.running:
            choice = self.getMenuOutput()

            if choice == 1:  # create
                self.createProject()

            elif choice == 2:  # build
                self.buildProject()

            elif choice == 3:  # edit
                self.editProject()

            elif choice == 4:  # exit
                self.exit()

    def getMenuOutput(self):
        """prints menu and returns selection"""
        print("######################################\n")
        print("Menu:\n")

        self.allProjectsFiles = self.returnFiles(settings.allProjectsDirectory)

        print()
        print("Choose what you wanna do:\n1) Create\n2) Build\n3) Edit\n4) Exit")

        choice = int(input("\nChoice: "))

        return choice

    def createProject(self):
        """create a new project, includes option to add files"""
        # makes new folder
        name = input("\nProject name: ")
        self.runTerminalCMD(["mkdir", name], settings.allProjectsDirectory)
        projectDirectory = settings.allProjectsDirectory + "/" + name
        makingFiles = True

        # option to add files
        while makingFiles:
            choice = int(input("\nAdd files?\n\t1) Yeah\n\t2) Nah\n\nChoice: "))
            if choice == 1:
                fileName = input("\nFile name: ")
                print()
                self.runTerminalCMD(["touch", fileName], projectDirectory)
                self.returnFiles(projectDirectory)

                if fileName == "main.cpp":
                    # if adding main.cpp, include commented block at top with data
                    self.templateFile(fileName, projectDirectory, "main")

                elif len(fileName) > 2 and fileName[-1] == 'h' and fileName[-2] == '.':
                    self.templateFile(fileName, projectDirectory, ".h")

                elif (len(fileName) > 4 and fileName[-1] == 'p' and fileName[-2] == 'p' and fileName[
                    -3] == 'c' and
                      fileName[-4] == '.'):
                    self.templateFile(fileName, projectDirectory, ".cpp")

            else:
                makingFiles = False

    def buildProject(self):
        """generate Makefile, compile, and compress project into .tar.gz"""
        # let user select project
        projects = {}
        enumHomeFiles = list(enumerate(self.allProjectsFiles, 1))

        for file in enumHomeFiles:
            projects[file[0]] = file[1]

        print("\nSelect project to build: ")
        counter = 1
        for i in range(len(enumHomeFiles)):
            print("\t" + str(counter) + ") " + str(projects[counter]))
            counter += 1

        choice = int(input("\nChoice: "))

        selectedProject = projects[choice]
        projectDirectory = settings.allProjectsDirectory + "/" + selectedProject

        projectFiles = self.returnFiles(projectDirectory, False)

        # make a new makefile
        if "Makefile" not in projectFiles:
            self.runTerminalCMD(["touch", "Makefile"], projectDirectory)

        # extract main.cpp and header files
        cppFiles = [file for file in projectFiles if
                    (file == "main.cpp" or (len(file) >= 3 and file[-1] == 'h' and file[-2] == '.'))]

        baseFiles = {}  # dependencies

        for file in cppFiles:

            # dict of main.cpp and header files; what other files they include; are they templated?
            baseFiles[file] = {"dependencies": [], "templated": False}

            filePath = projectDirectory + "/" + file
            # open main.cpp and each header file to see what they include
            fileObj = open(filePath, "r")
            content = fileObj.read().splitlines()
            potentialInludes = []

            for line in content:
                if "#include" in line:
                    potentialInludes.append(line)

            for dependencies in potentialInludes:
                words = dependencies.split()

                for word in words:
                    mod = word.replace("\"", "")

                    if len(mod) >= 3 and mod[-1] == 'h' and mod[-2] == '.' and mod in projectFiles:
                        # if .h file in loop includes another .h file
                        baseFiles[file]["dependencies"].append(mod)

                    elif len(mod) >= 5 and mod[-1] == 'p' and mod[-2] == 'p' and mod[-3] == 'c' and \
                            mod[-4] == '.' and mod in projectFiles:
                        # if .h file in loop includes a .cpp file (indicates its templated)
                        baseFiles[file]["templated"] = True

            fileObj.close()

        # start making the text to write into the makefile
        makefileOutput = "Main:"
        execStr = ""

        # dict to add the file.o clauses into to later add to makefile
        toMake = {}

        # for main.cpp and each .h header file
        for file in baseFiles:

            used = False
            for f in baseFiles:
                if file in baseFiles[f]["dependencies"]:
                    used = True

            # adding text to to_make and directly to makefile text
            # skip templated files bc they dont have their own .o clause in makefile
            # add_dependants() makes sure templated files are still included in the files that use them
            if not baseFiles[file]["templated"] and (used or file == "main.cpp"):
                # initialize cpp to false and to_add to file name
                isCPP = False
                toAdd = file
                if ".cpp" in file:
                    toAdd = toAdd.replace(".cpp", ".o")
                    isCPP = True
                    execStr += " " + toAdd
                    # file is main.cpp
                elif ".h" in file and file.replace(".h", ".cpp") in projectFiles:
                    toAdd = toAdd.replace(".h", ".o")
                    execStr += " " + toAdd

                if isCPP:  # refers to main.cpp
                    toMake[toAdd] = (toAdd + ": " + file)
                    self.addDependents(file, baseFiles, toMake, toAdd)
                    toMake[toAdd] += "\n\tg++ -std=c++11 -g -Wall -c main.cpp"

                elif file.replace(".h", ".cpp") in projectFiles:  # if file is a .h file
                    toMake[toAdd] = toAdd + ": " + file + " " + toAdd.replace(".o", ".cpp")
                    self.addDependents(file, baseFiles, toMake, toAdd)
                    toMake[toAdd] += "\n\tg++ -std=c++11 -g -Wall -c " + toAdd.replace(".o", ".cpp")

        makefileOutput += (execStr + "\n\tg++ -std=c++11 -g -Wall" + execStr + " -o Main")

        for dependent in toMake:
            makefileOutput += "\n\n" + toMake[dependent]

        makefileOutput += "\n\nclean:\n\trm *.o Main"

        makefile = open(projectDirectory + "/" + "Makefile", "w+")

        # write text to makefile
        makefile.write(makefileOutput)
        makefile.close()

        print("Would you like to compile?\n\t1) Yes\n\t2) No")
        shouldCompile = int(input("\nChoice: "))

        if shouldCompile == 1:
            # if not already compiled
            if "Main" not in projectFiles:
                self.runTerminalCMD("make", projectDirectory)

        # copy non .o files into new folder, make a copy of that folder, tar copied folder
        print("Would you like to compress files into tarred folder?\n\t1) Yes\n\t2) No")
        compress = int(input("\nChoice: "))
        if compress == 1:
            submission = settings.submissionName + selectedProject
            tarred = submission + ".tar.gz"
            # make new folder in project folder to copy files to; will be tarred
            self.runTerminalCMD(["mkdir", submission], projectDirectory)

            self.returnFiles(projectDirectory, False)

            for file in projectFiles:
                # copy files into new folder
                if file != "Main" and not (file[-1] == 'o' and file[-2] == '.') and file != submission:
                    self.runTerminalCMD(["cp", "-r", file, submission], projectDirectory)

            # tar folder
            self.runTerminalCMD(["tar", "-cvzf", tarred, submission], projectDirectory)

    def editProject(self):
        """lets user add files to project"""
        # select project to edit
        projects = {}
        enumHomeFiles = list(enumerate(self.allProjectsFiles, 1))

        for file in enumHomeFiles:
            projects[file[0]] = file[1]

        print("\nSelect project to edit: ")

        counter = 1

        for i in range(len(enumHomeFiles)):
            print("\t" + str(counter) + ") " + str(projects[counter]))
            counter += 1

        choice = int(input("\nChoice: "))

        selectedProject = projects[choice]
        projectDirectory = settings.allProjectsDirectory + "/" + selectedProject

        self.returnFiles(projectDirectory, False)

        # add files to project folder
        makingFiles = True
        firstTime = True
        while makingFiles:

            if not firstTime:
                choice = int(input("\nAdd files?\n\t1) Yeah\n\t2) Nah\n\nChoice: "))
            else:
                choice = 1

            if choice == 1:
                # get name of file to add
                fileName = input("\nFile name: ")
                print()
                self.runTerminalCMD(["touch", fileName], projectDirectory)
                self.returnFiles(projectDirectory)

                if fileName == "main.cpp":
                    # if adding main.cpp, include commented block at top with data
                    self.templateFile(fileName, projectDirectory, "main")

                elif len(fileName) > 2 and fileName[-1] == 'h' and fileName[-2] == '.':
                    self.templateFile(fileName, projectDirectory, ".h")

                elif (len(fileName) > 4 and fileName[-1] == 'p' and fileName[-2] == 'p'
                      and fileName[-3] == 'c' and fileName[-4] == '.'):
                    self.templateFile(fileName, projectDirectory, ".cpp")

            else:
                makingFiles = False

            firstTime = False

    def exit(self):
        """exits program"""
        self.running = False

    @staticmethod
    def runTerminalCMD(cmd, directory, itemizeOutput=True):
        """runs command in terminal from directory"""
        out = subprocess.Popen(cmd,
                               cwd=directory,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True)

        stdout, stderr = out.communicate()

        if itemizeOutput:
            stdout = stdout.split()

        if str(stderr) != "None":
            print("Process has raised an exception")

        return stdout

    def returnFiles(self, directory, printOutput=True):
        """gets, optionally prints, and returns all files in directory"""
        files = self.runTerminalCMD("ls", directory)
        if "ProjectManager" in files:
            files.remove("ProjectManager")
        if printOutput:
            print("Files in " + directory + ":")
            for file in files:
                print("\t" + str(file))
        return files

    def addDependents(self, file, baseFiles, toMake, toAdd):  # recursion
        """add dependent includes and files to basefiles to generate Makefile"""
        if not baseFiles[file]["dependencies"]:
            return
        else:
            for dependent in baseFiles[file]["dependencies"]:
                if dependent not in toMake[toAdd]:
                    toMake[toAdd] += " " + dependent
                if baseFiles[dependent]["templated"]:
                    if dependent.replace(".h", ".cpp") not in toMake[toAdd]:
                        toMake[toAdd] += " " + dependent.replace(".h", ".cpp")
                        self.addDependents(dependent, baseFiles, toMake, toAdd)

    @staticmethod
    def templateFile(name, directory, fileType):
        """creates custom template to file based on file type (main.cpp, .h, .cpp)"""
        file = open(directory + "/" + name, "w+")

        if fileType == ".cpp":
            file.write(
                "/**\n *@Name: " + settings.name + "\n *@File: " + name + "\n *@Date: " + str(
                    date.today()) + "\n *@Description: \n**/\n\n")

            file.write("#include \"" + name.replace(".cpp", ".h") + "\"")

        elif fileType == ".h":
            file.write(
                "/**\n *@Name: " + settings.name + "\n *@File: " + name + "\n *@Date: " + str(
                    date.today()) + "\n *@Description: \n**/\n\n")
            file.write("#ifndef " + (name.replace(".h", "_H").upper()))
            file.write("\n#define " + (name.replace(".h", "_H").upper()))
            class_name = name.replace(".h", "")
            class_name = class_name[0].upper() + class_name[1:]
            file.write("\n\nclass " + class_name + " {\n\nprivate:\n\npublic:\n\n};\n\n#endif")

        elif fileType == "main":
            file.write(
                "/**\n *@Name: " + settings.name + "\n *@ID: " + settings.ID +
                "\n *@Assignment: " + name + "\n *@File: main.cpp" + "\n *@Date: " +
                str(date.today()) + "\n *@Description: \n**/\n\nint main(int argc, char* argv[]) {\n\n\n\nreturn 0; }")

        file.close()
