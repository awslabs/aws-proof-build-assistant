import argparse

NAME = "aquifer"

def build():
    print("build is not yet implemented")

def print_file(file):
    print("print is not yet implemented")

def render():
    print("render is not yet implemented")


def main():
    description = NAME + " tool: helping developers get build information for cource files they want to test."

    parser = argparse.ArgumentParser(description=description)

    # parser.add_argument("--build", action="store_true", help="buld JSON database for mapping source files to build information")
    # parser.add_argument("--print", default='', help="print build information for a given source file")
    # parser.add_argument("--render", action="store_true", help="generate a web interface to browse {} database".format(NAME))
    parser.add_argument("command", nargs="+", default = "", help="run command for {}. Available command: build, print <SRC_FILE>, render".format(NAME))
    arguments = parser.parse_args()

    valid_commands = ["build", "print", "render"]
    cmd = arguments.command[0]
    cmd_args = arguments.command[1:]
    num_args = len(cmd_args)

    if not cmd in valid_commands:
        print("Please input a valid command: " + str(valid_commands))

    #error cases
    error = num_args > 1 or (num_args > 0 and (cmd == "build" or cmd == "render"))

    if error :
        print("Too many Arguments!")
        return

    if cmd == "build":
        build()

    if cmd == "print":
        if num_args == 0 : 
            print("Please add the file to print build information for: print <SRC_FILE>")
        else:
            print_file(cmd_args[0])

    if cmd == "render":
        render()




if __name__== "__main__":
    main()