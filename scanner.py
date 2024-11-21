import re
from PyQt5.QtGui import QTextCursor
import PyQt5.QtWidgets
import os
import numpy as np
import pandas as pd
from gui import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
import sys





class Back_End_Class(QtWidgets.QWidget, Ui_MainWindow):

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.setupUi(MainWindow)
        self.thread = {}
        self.scan.clicked.connect(self.Scan)

    def Scan(self):
        print("Enter tiny language code (end with an empty line):")
        user_input = self.input.toPlainText().splitlines()
        user_code = "\n".join(user_input)

        # Initialize scanner and perform scanning
        scanner = Scanner()
        scanner.scan(user_code)
        scanner.output()  # Save output to file

        # Display tokens and errors in the QTextBrowser
        output_content = []
        output_content.append("Tokens:\n")
        output_content.append(f"{'Line':<5} {'Token':<12} {'Type':<12}\n")
        output_content.append(f"{'====':<5} {'====':<12} {'=====':<12}\n")
        for line_number, token, token_type in scanner.tokens:
            output_content.append(f"{line_number:<5} {token:<12} {token_type:<12}\n")

        if scanner.errors:
            output_content.append("\nErrors:\n")
            for line_number, error in scanner.errors:
                output_content.append(f"Line {line_number}: {error}\n")

        # Join the content for display
        self.output.setPlainText("".join(output_content))  # Assuming `output_text` is a QTextBrowser in your UI


class Scanner:
    STATES = {
        'START': False,
        'IN_COMMENT': False,
        'IN_ID': False,
        'IN_NUM': False,
        'IN_ASSIGN': False,
        'DONE': False,
        'OTHER': False
    }

    def __init__(self):
        self.set_state('START')
        self.tokens = []
        self.errors = []
        self.state_other = False

    def set_state(self, state):
        for key in self.STATES:
            self.STATES[key] = False
        self.STATES[state] = True

    def get_state(self, state):
        return self.STATES[state]

    def scan(self, input_text): #DFA implementation to scan input string as separate lines
        lines = input_text.splitlines()
        for line_number, line in enumerate(lines, start=1):
            token = ''
            for i, c in enumerate(line + ' '):  # Add space to force DONE state at end

                #Start State#

                if self.get_state('START'):
                    if self.is_symbol(c):
                        self.set_state('DONE')
                    elif c == ' ':
                        self.set_state('START')
                        continue
                    elif c == '{':
                        self.set_state('IN_COMMENT')
                    elif self.is_num(c):
                        self.set_state('IN_NUM')
                    elif self.is_str(c):
                        self.set_state('IN_ID')
                    elif self.is_col(c):
                        self.set_state('IN_ASSIGN')

                #IN_COMMENT state#

                elif self.get_state('IN_COMMENT'):
                    if c == '}':
                        self.set_state('DONE')
                    else:
                        self.set_state('IN_COMMENT')

                #IN_NUMBER state#

                elif self.get_state('IN_NUM'):
                    if self.is_num(c):
                        self.set_state('IN_NUM')
                    elif c == ' ':
                        self.set_state('DONE')
                    else:
                        self.set_state('OTHER')

                #IN_IDENTIFIER state#

                elif self.get_state('IN_ID'):
                    if self.is_str(c):
                            self.set_state('IN_ID')
                    elif c == ' ':
                        self.set_state('DONE')
                    else:
                        self.set_state('OTHER')

                #IN_ASSIGNMENT state#

                elif self.get_state('IN_ASSIGN'):
                    if c == '=':
                        self.set_state('DONE')
                    else:
                        # Report ":" as an error if not followed by "="
                        self.errors.append((line_number, "':' is not followed by '='"))
                        self.classify(':', line_number)  # Classify the colon as an invalid token
                        self.set_state('START')  # Reset state to process the next token
                        token = ''  # Clear the token
                        continue  # Reprocess current character as part of the next token


                if not self.get_state('OTHER'): #Retrieve tokens#
                    token += c

                if self.get_state('OTHER'):
                    self.set_state('DONE')
                    self.state_other = True

                #DONE state#

                if self.get_state('DONE'):
                    self.classify(token, line_number)
                    if self.state_other:
                        token = c
                        if self.is_col(c): self.set_state('IN_ASSIGN')
                        if self.is_comment(c): self.set_state('IN_COMMENT')
                        if self.is_num(c): self.set_state('IN_NUM')
                        if self.is_str(c): self.set_state('IN_ID')
                        if self.is_symbol(c):
                            self.classify(c, line_number)
                            token = ''
                            self.set_state('START')
                        self.state_other = False
                    else:
                        token = ''
                    self.set_state('START')

    KEYWORDS = ['else', 'end', 'if', 'repeat', 'then', 'until', 'read', 'write']

    OPERATORS = {
        '+'         : 'PLUS',
        '-'         : 'MINUS',
        '*'         : 'MULT',
        '/'         : 'DIV',
        ':'         : 'COLON',
        '='         : 'EQUAL',
        ':='        : 'ASSIGN',
        '<'         : 'LESSTHAN',
        ';'         : 'SEMICOLON',
        '('         : 'OPENBRACKET',
        ')'         : 'CLOSEDBRACKET'
    }

    def classify(self, token, line_number):
        if not token:
            return  # Skip empty tokens
        if token[-1:] == ' ':
            token = token[0:-1]

        if self.is_str(token):
            if token in self.KEYWORDS:
                self.tokens.append((line_number, token, token.upper()))
            else:
                self.tokens.append((line_number, token, 'IDENTIFIER'))
        elif self.is_num(token):
            self.tokens.append((line_number, token, 'NUMBER'))
        elif token in self.OPERATORS:
            self.tokens.append((line_number, token, self.OPERATORS[token]))
        elif self.is_comment(token):
            self.tokens.append((line_number, token, 'COMMENT'))
        elif token == ':':
            self.errors.append((line_number, "Unidentified token: ':'"))
        else:
            self.errors.append((line_number, f"Invalid token: {token}"))

    #Helper functions#

    def is_str(self, token):
        return token.isalpha() #checks if all values of input string are alphabetical

    def is_num(self, token):
        return token.isdigit() #checks if all values of input string are numerical

    def is_col(self, c):
        return c == ':' #check for a colon : for the := operator

    def is_symbol(self, token):
        return token in ['+', '-', '*', '/', '=', '<', '>', '(', ')', ';'] #checks valid symbols

    def is_comment(self, token):
        return re.match(r'^{.+}$', token) is not None

    #output as .txt file#

    def output(self, output_file='scanner_output.txt'):
        with open(output_file, 'w') as file:
            file.write("Tokens:\n")
            file.write(f"{'Line':<5} {'Token':<12} {'Type':<12}\n")
            file.write(f"{'====':<5} {'====':<12} {'=====':<12}\n")
            for line_number, token, token_type in self.tokens:
                file.write(f"{line_number:<5} {token_type:<12} {token:<12}\n")

            if self.errors:
                file.write("\nErrors:\n")
                for line_number, error in self.errors:
                    file.write(f"Line {line_number}: {error}\n")

        #Optionally display the output in the console to quick test
        """
        print("\nTokens:")
        print(f"{'Line':<5} {'Token':<12} {'Type':<12}")
        print(f"{'====':<5} {'====':<12} {'=====':<12}")
        for line_number, token, token_type in self.tokens:
            print(f"{line_number:<5} {token_type:<12} {token:<12}")
        
        if self.errors:
            print("\nErrors:")
            for line_number, error in self.errors:
                print(f"Line {line_number}: {error}")
        
        print(f"\nOutput saved to '{output_file}'")"""


# def main():
#     #testing#
#     print("Enter tiny language code (end with an empty line):")
#     user_input = []
#     while True:
#         line = input()
#         if line == "":
#             break
#         user_input.append(line)
#     user_code = "\n".join(user_input)
#
#     scanner = Scanner()
#     scanner.scan(user_code)
#     scanner.output()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Back_End_Class()
    MainWindow.show()
    sys.exit(app.exec_())
