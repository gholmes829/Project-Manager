"""
Author: Grant Holmes
Contact: g.holmes429@gmail.com
Date: Early Summer 2020

Description: This program manages files for C++ projects. Setup preferences in settings.py.
                Functions:
                            1) Create - create new project, add files
                            2) Build - auto generate Makefile, compile project, compress project
                            3) Edit - add files to project

                Templating:
                            Program auto template main.cpp, .cpp, and .h files for convenience

                Runs on Linux, and need to have following file structure:
                                Folder with all projects -> # Project -> project files
                                                            # Project -> project files
                                                            # ...
                                                            # Project -> project files
"""

from core.driver import Driver


def main():
    driver = Driver()
    driver.run()


if __name__ == "__main__":
    main()
