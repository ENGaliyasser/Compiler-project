class Node:
    """A class to represent a node in the syntax tree."""

    def __init__(self, name, shape):
        self.name = name  # Name of the node (e.g., "if", "repeat", "assign(x)")
        self.children = []  # List to store child nodes
        self.sibling = None  # Pointer to the next sibling node
        self.shape = shape  # Shape of the node when visualized ("oval" or "rectangle")
        self.x = 0  # X-coordinate for positioning (used in GUI visualization)
        self.y = 0  # Y-coordinate for positioning (used in GUI visualization)

    def add_child(self, child):
        """Add a child node to the current node."""
        self.children.append(child)

    def add_sibling(self, sibling_node):
        """Add a sibling node to the current node."""
        if not isinstance(sibling_node, Node):
            raise ValueError("Sibling must be an instance of Node")

        # Traverse to the last sibling in the chain
        current = self
        while current.sibling:
            current = current.sibling

        # Attach the new sibling at the end
        current.sibling = sibling_node

    def __str__(self, level=0):
        """
        Recursively create a string representation of the tree structure,
        including siblings, for printing purposes.
        """
        ret = "  " * level + f"{self.name}\n"  # Indentation based on the level
        for child in self.children:
            ret += child.__str__(level + 1)  # Recurse for child nodes

        # Include siblings at the same level
        if self.sibling:
            ret += self.sibling.__str__(level)

        return ret

operators = [')', '(', ';', '<', '=', '/', ':=', '*', '-', '+']  # List of operator tokens

class ParserError(Exception):
    """Custom exception class for parser errors."""
    pass

class Parser:
    """A recursive descent parser for the given grammar."""

    def __init__(self, tokens_list):
        """Initialize the parser with a list of tokens."""
        self.tokens_list = tokens_list  # The list of tokens to parse
        self.current_token_index = 0  # Index of the current token in the list
        self.current_token = None  # The current token
        self.advance()  # Initialize with the first token
        self.errors = []  # List to store error messages

    def advance(self):
        """Advance to the next token in the tokens list."""
        if self.current_token_index < len(self.tokens_list):
            self.current_token = self.tokens_list[self.current_token_index]
            self.current_token_index += 1
            print(f"Advanced to token: {self.current_token}")
        else:
            self.current_token = None  # No more tokens; end of token stream
            print("End of token stream reached.")

    def error(self, message):
        """Handle an error by appending an error message and raising an exception."""
        error_message = f"Syntax Error: {message}"
        print(error_message)
        self.errors.append(error_message)  # Record the error
        raise ParserError(error_message)  # Raise a ParserError to halt parsing

    def match(self, expected):
        """
        Match the current token with an expected value or type.
        If matched, advance to the next token and return a Node.
        """
        print(f"Matching token: {self.current_token} with expected: {expected}")
        if self.current_token:
            token_value, token_type = self.current_token
            if expected == token_type or expected == token_value:
                matched_token = self.current_token  # Save the matched token
                self.advance()  # Move to the next token

                # Create and return a Node based on the token type
                if expected == "NUMBER":
                    return Node(f"const({matched_token[0]})", "oval")
                elif expected == "REPEAT":
                    return Node("repeat", "rectangle")
                elif expected in operators:
                    return Node(f"op({matched_token[0]})", "oval")
                elif expected == "IDENTIFIER":
                    return Node(f"id({matched_token[0]})", "oval")
                else:
                    return Node(matched_token[0], "oval")  # Default case
        # If no match, raise an error
        self.error(f"Expected {expected}, found {self.current_token}")

    def check_for_semicolon(self):
        """
        Ensure the current statement is followed by a semicolon,
        unless it's the last statement in a block.
        """
        if self.current_token is None:
            return  # End of program; no semicolon required

        # Check if the next token is a semicolon
        if self.current_token and self.current_token[0] != ';':
            self.error("Expected ';' after statement, found: " + str(self.current_token))
        elif self.current_token:
            self.match(';')  # Consume the semicolon

    def program(self):
        """Parse the program starting point according to the grammar."""
        print("Parsing program.")
        program_node = self.stmt_sequence()  # Parse a sequence of statements
        if self.current_token:
            # If there are unexpected tokens after parsing
            self.error("Unexpected token after program. Found: " + str(self.current_token))
        return program_node  # Return the root node of the syntax tree

    def stmt_sequence(self):
        """Parse a sequence of statements."""
        print("Parsing stmt-sequence.")
        stmt_seq_node = self.statement()  # Parse the first statement

        while self.current_token:
            # Check for a semicolon between statements
            if self.current_token[0] == ';':
                print("Found semicolon in stmt-sequence.")
                self.match(';')  # Consume the semicolon
                stmt_seq_node.add_sibling(self.statement())  # Parse the next statement and add it as a sibling
            elif self.current_token[0] in {'end', 'else', 'until'}:
                # If the current token is a block-ending token, stop parsing the sequence
                print("End of stmt-sequence due to block-ending token.")
                break
            else:
                # If the token isn't a semicolon or block-ending token, it's an error
                self.error(f"Syntax error, unexpected token: {self.current_token}")

        return stmt_seq_node  # Return the node representing the statement sequence

    def statement(self):
        """Parse a single statement."""
        print(f"Parsing statement. Current token: {self.current_token}")
        if self.current_token[1] == 'IF':
            return self.if_stmt()
        elif self.current_token[1] == 'REPEAT':
            return self.repeat_stmt()
        elif self.current_token[1] == 'IDENTIFIER':
            return self.assign_stmt()
        elif self.current_token[1] == 'READ':
            return self.read_stmt()
        elif self.current_token[1] == 'WRITE':
            return self.write_stmt()
        else:
            self.error("Invalid statement type or missing keyword")

    def if_stmt(self):
        """Parse an if-statement."""
        print("Parsing if-stmt.")
        if_node = Node("if", "rectangle")  # Create an 'if' node
        self.match('IF')  # Match the 'if' keyword
        if_node.add_child(self.exp())  # Parse the condition expression and add it as a child
        self.match('THEN')  # Match the 'then' keyword
        if_node.add_child(self.stmt_sequence())  # Parse the 'then' part statements

        if self.current_token and self.current_token[0] == 'else':
            # Handle the optional 'else' part
            print("Found ELSE in if-stmt.")
            self.match('ELSE')  # Match the 'else' keyword
            if_node.add_child(self.stmt_sequence())  # Parse the 'else' part statements

        if self.current_token and self.current_token[0] != 'end':
            # If 'end' is missing after the 'if' statement
            self.error("Expected 'END' after 'if' statement.")
        self.match('END')  # Match the 'end' keyword
        return if_node  # Return the 'if' node

    def repeat_stmt(self):
        """Parse a repeat-statement."""
        print("Parsing repeat-stmt.")
        repeat_node = self.match('REPEAT')  # Match the 'repeat' keyword and create a node
        repeat_node.add_child(self.stmt_sequence())  # Parse the statements inside the repeat
        if self.current_token and self.current_token[0] != 'until':
            # If 'until' is missing after the repeat statements
            self.error("Expected 'UNTIL' after repeat statement.")
        self.match('UNTIL')  # Match the 'until' keyword
        repeat_node.add_child(self.exp())  # Parse the condition expression
        return repeat_node  # Return the 'repeat' node

    def assign_stmt(self):
        """Parse an assignment-statement."""
        print("Parsing assign-stmt.")
        temp_node = self.match('IDENTIFIER')  # Match an identifier (variable name)
        assign_node = Node(f"assign({temp_node.name})", "rectangle")  # Create an 'assign' node
        self.match(':=')  # Match the assignment operator ':='
        assign_node.add_child(self.exp())  # Parse the expression being assigned
        return assign_node  # Return the 'assign' node

    def read_stmt(self):
        """Parse a read-statement."""
        print("Parsing read-stmt.")
        self.match('READ')  # Match the 'read' keyword
        temp_node = self.match('IDENTIFIER')  # Match the identifier to read into
        read_node = Node(f"read({temp_node.name})", "rectangle")  # Create a 'read' node
        return read_node  # Return the 'read' node

    def write_stmt(self):
        """Parse a write-statement."""
        print("Parsing write-stmt.")
        write_node = Node("write", "rectangle")  # Create a 'write' node
        self.match('WRITE')  # Match the 'write' keyword
        write_node.add_child(self.exp())  # Parse the expression to be written
        return write_node  # Return the 'write' node

    def exp(self):
        """Parse an expression."""
        print("Parsing exp.")
        temp_node = self.simple_exp()  # Parse a simple expression
        if self.current_token and self.current_token[0] in ['<', '=']:
            # If there's a comparison operator, create a new node
            print(f"Found comparison operator: {self.current_token[0]}")
            new_temp = self.match(self.current_token[0])  # Match the operator
            new_temp.add_child(temp_node)  # Add left operand
            new_temp.add_child(self.simple_exp())  # Parse and add right operand
            temp_node = new_temp  # Update the temporary node
        return temp_node  # Return the expression node

    def simple_exp(self):
        """Parse a simple expression consisting of terms and add operators."""
        print("Parsing simple-exp.")
        temp_node = self.term()  # Parse the first term
        while self.current_token and self.current_token[0] in ['+', '-']:
            # While there are add operators, create new nodes
            print(f"Found addop: {self.current_token[0]}")
            new_temp = self.match(self.current_token[0])  # Match the '+' or '-' operator
            new_temp.add_child(temp_node)  # Add left operand
            new_temp.add_child(self.term())  # Parse and add right operand
            temp_node = new_temp  # Update the temporary node
        return temp_node  # Return the simple expression node

    def term(self):
        """Parse a term consisting of factors and multiply operators."""
        print("Parsing term.")
        temp_node = self.factor()  # Parse the first factor
        while self.current_token and self.current_token[0] in ['*', '/']:
            # While there are multiply operators, create new nodes
            print(f"Found mulop: {self.current_token[0]}")
            new_temp = self.match(self.current_token[0])  # Match the '*' or '/' operator
            new_temp.add_child(temp_node)  # Add left operand
            new_temp.add_child(self.factor())  # Parse and add right operand
            temp_node = new_temp  # Update the temporary node
        return temp_node  # Return the term node

    def factor(self):
        """Parse a factor, which could be a number, an identifier, or an expression in parentheses."""
        print(f"Parsing factor. Current token: {self.current_token}")
        if self.current_token:
            token_value, token_type = self.current_token
            if token_type == "NUMBER":
                return self.match("NUMBER")  # Match and return a number node
            elif token_type == "IDENTIFIER":
                return self.match("IDENTIFIER")  # Match and return an identifier node
            elif token_value == "(":
                # Handle expressions in parentheses
                self.match("(")  # Match the opening parenthesis
                expr_node = self.exp()  # Parse the inner expression
                self.match(")")  # Match the closing parenthesis
                return expr_node  # Return the expression node
            else:
                # Invalid factor
                self.error("Invalid factor")
        # If current token is None or invalid
        self.error("Invalid factor")