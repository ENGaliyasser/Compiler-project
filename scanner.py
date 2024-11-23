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


keywords = ['read', 'if', 'then', 'repeat', 'until', 'write', 'end']


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
        self.in_comment_block = False  # Track if inside a multiline comment

    def set_state(self, state):
        for key in self.STATES:
            self.STATES[key] = False
        self.STATES[state] = True

    def get_state(self, state):
        return self.STATES[state]

    def scan(self, input_text):
        global comment_line
        lines = input_text.splitlines()
        stop_parsing = False  # Flag to indicate parsing should stop

        for line_number, line in enumerate(lines, start=1):
            if stop_parsing:
                break  # Stop parsing if the flag is set

            if not self.in_comment_block:
                self.set_state('START')

            token = ''
            i = 0
            while i < len(line):
                if stop_parsing:
                    break  # Stop parsing if the flag is set

                c = line[i]

                if self.in_comment_block:
                    # Handle multiline comments
                    if c == '}':
                        self.in_comment_block = False
                    elif c == '{':
                        self.errors.append((line_number, f"NOT ALLOWED NESTED COMMENT"))
                        stop_parsing = True  # Set the flag to stop parsing
                        break  # Break out of the current loop
                    i += 1
                    continue

                # Start state
                if self.get_state('START'):
                    if c == '{':
                        comment_line = line_number
                        self.in_comment_block = True
                    elif c == ':':
                        if i+1 == len(line):
                            self.errors.append((line_number, f"Invalid token: {c}"))
                            stop_parsing = True  # Set the flag to stop parsing
                            break  # Break out of the current loop
                        self.set_state('IN_ASSIGN')
                    elif self.is_symbol(c):
                        self.classify(c, line_number)
                    elif self.is_num(c):
                        self.set_state('IN_NUM')
                        token = c
                    elif self.is_str(c):
                        self.set_state('IN_ID')
                        token = c
                    elif c == ' ':
                        # Ignore spaces
                        pass
                    else:
                        self.errors.append((line_number, f"Invalid token: {c}"))
                        stop_parsing = True  # Set the flag to stop parsing
                        break  # Break out of the current loop

                # IN_ASSIGN state
                elif self.get_state('IN_ASSIGN'):
                    if c == '=':
                        self.classify(":=", line_number)  # Valid ASSIGN token
                    else:
                        self.errors.append((line_number, "Invalid token: ':'"))  # Standalone `:` is invalid
                        stop_parsing = True  # Set the flag to stop parsing
                        break  # Break out of the current loop
                    self.set_state('START')

                # IN_NUM state (modified)
                elif self.get_state('IN_NUM'):
                    if self.is_num(c):
                        token += c
                    elif c == ' ' or c == ';' or c == '\n':
                        # Space, semicolon, or newline marks the end of a valid token
                        self.classify(token, line_number)
                        token = ''
                        if c == ';':
                            self.classify(c, line_number)  # Treat semicolon as a separate token
                        self.set_state('START')
                    else:
                        # If an invalid character is found, log an error and discard the rest of the number
                        error_token = token + c  # Start with the current invalid character
                        while i + 1 <= len(line) and line[i + 1] not in [' ', ';', '\n']:
                            i += 1
                            error_token += line[i]
                        self.errors.append((line_number, f"INVALID NUMBER: {error_token}"))
                        stop_parsing = True  # Set the flag to stop parsing
                        break  # Break out of the current loop
                        token = ''  # Discard the token completely
                        self.set_state('START')

                # IN_ID state
                elif self.get_state('IN_ID'):
                    if self.is_str(c):
                        token += c
                    elif c == ' ' or c == ';':
                        # Space or semicolon marks the end of a valid token
                        self.classify(token, line_number)
                        token = ''
                        if c == ';':
                            self.classify(c, line_number)  # Treat semicolon as a separate token
                        self.set_state('START')
                    else:
                        # If an invalid character is found, log an error and discard the rest of the identifier
                        error_token = token + c  # Start with the current invalid character
                        while i + 1 < len(line) and line[i + 1] not in [' ', ';']:
                            i += 1
                            error_token += line[i]
                        self.errors.append((line_number, f"INVALID IDENTIFIER: {error_token}"))
                        stop_parsing = True  # Set the flag to stop parsing
                        break  # Break out of the current loop
                        token = ''  # Discard the token completely
                        self.set_state('START')

                i += 1

            # Finalize tokens at the end of the line
            if token and not stop_parsing:
                self.classify(token, line_number)

        if self.in_comment_block and not stop_parsing:
            self.errors.append((comment_line, f"UNCLOSED COMMENT"))

    KEYWORDS = ['else', 'end', 'if', 'repeat', 'then', 'until', 'read', 'write']

    OPERATORS = {
        '+': 'PLUS',
        '-': 'MINUS',
        '*': 'MULT',
        '/': 'DIV',
        ':=': 'ASSIGN',
        '=': 'EQUAL',
        '<': 'LESSTHAN',
        ';': 'SEMICOLON',
        '(': 'OPENBRACKET',
        ')': 'CLOSEDBRACKET'
    }

    def classify(self, token, line_number):
        if not token:
            return  # Skip empty tokens
        if self.is_str(token):
            if token in self.KEYWORDS:
                self.tokens.append((line_number, token, token.upper()))
            else:
                self.tokens.append((line_number, token, 'IDENTIFIER'))
        elif self.is_num(token):
            self.tokens.append((line_number, token, 'NUMBER'))
        elif token in self.OPERATORS:
            self.tokens.append((line_number, token, self.OPERATORS[token]))
        else:
            self.errors.append((line_number, f"Invalid token: {token}"))

    # Helper functions
    def is_str(self, token):
        return token.isalpha()

    def is_num(self, token):
        return token.isdigit()

    def is_symbol(self, token):
        return token in ['+', '-', '*', '/', '=', '<', ';', '(', ')']

    # Output as .txt file
    def output(self, output_file='scanner_output.txt'):
        with open(output_file, 'w') as file:
            file.write("Tokens:\n")
            file.write(f"{'Line':<5} {'Token':<12} {'Type':<12}\n")
            file.write(f"{'====':<5} {'====':<12} {'=====':<12}\n")
            for line_number, token, token_type in self.tokens:
                file.write(f"{line_number:<5} {token:<12} {token_type:<12}\n")

            if self.errors:
                file.write("\nErrors:\n")
                for line_number, error in self.errors:
                    file.write(f"Line {line_number}: {error}\n")





if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Back_End_Class()
    MainWindow.show()
    sys.exit(app.exec_())
