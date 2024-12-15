
class Node:
    """A class to represent a node in the syntax tree."""

    def __init__(self, name, shape):
        self.name = name
        self.children = []
        self.sibling = None  # Pointer to the next sibling node
        self.shape = shape

    def add_child(self, child):
        """Add a child node."""
        self.children.append(child)

    def add_sibling(self, sibling_node):
        """Add a sibling node."""
        if not isinstance(sibling_node, Node):
            raise ValueError("Sibling must be an instance of Node")

        # Traverse to the last sibling
        current = self
        while current.sibling:
            current = current.sibling

        # Attach the new sibling
        current.sibling = sibling_node

    def __str__(self, level=0):
        """Recursively print the tree structure, including siblings."""
        ret = "  " * level + f"{self.name}{level: {level}}\n"
        for child in self.children:
            ret += child.__str__(level + 1)

        # Print siblings at the same level
        if self.sibling:
            ret += self.sibling.__str__(level)

        return ret



operators = [')' , '(' , ';' , '<' , '=' , '/' , ':=' , '*' , '-' , '+' ]
class Parser:
    def __init__(self, tokens_list):
        """Initialize the parser with a list of tokens."""
        self.tokens_list = tokens_list
        self.current_token_index = 0
        self.current_token = None
        self.advance()  # Initialize with the first token

    def advance(self):
        """Move to the next token."""
        if self.current_token_index < len(self.tokens_list):
            self.current_token = self.tokens_list[self.current_token_index]
            self.current_token_index += 1
            print(f"Advanced to token: {self.current_token}")
        else:
            self.current_token = None  # End of token stream
            print("End of token stream reached.")

    def error(self, message):
        """Raise an error with a message."""
        print(f"Syntax Error: {message}")
        raise SyntaxError(message)

    def match(self, expected):
        """Match the current token with an expected value or type."""
        print(f"Matching token: {self.current_token} with expected: {expected}")
        if self.current_token:
            token_value, token_type = self.current_token
            if expected == token_type or expected == token_value:
                matched_token = self.current_token
                self.advance()
                if expected == "NUMBER":
                    return Node(f"const({matched_token[0]})","oval")
                elif expected == "REPEAT":
                    return Node("repeat","rectangle")
                elif expected in operators:
                    return Node(f"op({matched_token[0]})","oval")
                elif expected == "IDENTIFIER":
                    return Node(f"id({matched_token[0]})","oval")
                else:
                    return Node(matched_token[0],"oval")  # Return the token value as a Node
        self.error(f"Expected {expected}, found {self.current_token}")

    def check_for_semicolon(self):
        """Ensure the current statement is followed by a semicolon, unless it's the last statement."""
        if self.current_token is None:
            return  # End of program, no semicolon required

        # Check if the next token is a semicolon
        if self.current_token and self.current_token[0] != ';':
            self.error("Expected ';' after statement, found: " + str(self.current_token))
        elif self.current_token:
            self.match(';')  # Consume the semicolon

    def program(self):
        """Parse the program rule."""
        print("Parsing program.")
        program_node = self.stmt_sequence()
        if self.current_token:
            self.error("Unexpected token after program. Found: " + str(self.current_token))
        return program_node

    def stmt_sequence(self):
        """Parse the stmt-sequence rule."""
        print("Parsing stmt-sequence.")
        stmt_seq_node = self.statement()

        while self.current_token:
            # Check for a semicolon
            if self.current_token[0] == ';':
                print("Found semicolon in stmt-sequence.")
                self.match(';')  # Consume the semicolon
                stmt_seq_node.add_sibling(self.statement())  # Parse the next statement
            elif self.current_token[0] in {'end', 'else','until'}:
                # Block-ending tokens: stop parsing the sequence
                print("End of stmt-sequence due to block-ending token.")
                break
            else:
                # Error if the token isn't a semicolon or block-ending
                self.error(f"Syntax error, unexpected token: {self.current_token}")

        return stmt_seq_node

    def statement(self):
        """Parse the statement rule."""
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
        """Parse the if-stmt rule."""
        print("Parsing if-stmt.")
        if_node = Node("if","rectangle")
        self.match('IF')
        if_node.add_child(self.exp())
        self.match('THEN')
        if_node.add_child(self.stmt_sequence())
        if self.current_token and self.current_token[0] == 'else':
            print("Found ELSE in if-stmt.")
            self.match('ELSE')
            if_node.add_child(self.stmt_sequence())
        if self.current_token and self.current_token[0] != 'end':
            self.error("Expected 'END' after 'if' statement.")
        self.match('END')
        return if_node

    def repeat_stmt(self):
        """Parse the repeat-stmt rule."""
        print("Parsing repeat-stmt.")
        repeat_node = self.match('REPEAT')
        repeat_node.add_child(self.stmt_sequence())
        if self.current_token and self.current_token[0] != 'until':
            self.error("Expected 'UNTIL' after repeat statement.")
        self.match('UNTIL')
        repeat_node.add_child(self.exp())
        return repeat_node

    def assign_stmt(self):
        """Parse the assign-stmt rule."""
        print("Parsing assign-stmt.")
        temp_node = self.match('IDENTIFIER')
        assign_node = Node(f"assign({temp_node.name})","rectangle")
        self.match(':=')
        assign_node.add_child(self.exp())
        return assign_node

    def read_stmt(self):
        """Parse the read-stmt rule."""
        print("Parsing read-stmt.")
        self.match('READ')
        temp_node = self.match('IDENTIFIER')
        read_node = Node(f"read({temp_node.name})", "rectangle")
        return read_node

    def write_stmt(self):
        """Parse the write-stmt rule."""
        print("Parsing write-stmt.")
        write_node = Node("write","rectangle")
        self.match('WRITE')
        write_node.add_child(self.exp())
        return write_node

    def exp(self):
        """Parse the exp rule."""
        print("Parsing exp.")
        temp_node = self.simple_exp()
        if self.current_token and self.current_token[0] in ['<', '=']:
            print(f"Found comparison operator: {self.current_token[0]}")
            new_temp = self.match(self.current_token[0])
            new_temp.add_child(temp_node)
            new_temp.add_child(self.simple_exp())
            temp_node = new_temp
        return temp_node

    def simple_exp(self):
        """Parse the simple-exp rule."""
        print("Parsing simple-exp.")
        temp_node = self.term()
        while self.current_token and self.current_token[0] in ['+', '-']:
            print(f"Found addop: {self.current_token[0]}")
            new_temp = self.match(self.current_token[0])
            new_temp.add_child(temp_node)
            new_temp.add_child(self.term())
            temp_node = new_temp
        return temp_node

    def term(self):
        """Parse the term rule."""
        print("Parsing term.")
        temp_node = self.factor()
        while self.current_token and self.current_token[0] in ['*', '/']:
            print(f"Found mulop: {self.current_token[0]}")
            new_temp = self.match(self.current_token[0])
            new_temp.add_child(temp_node)
            new_temp.add_child(self.factor())
            temp_node = new_temp
        return temp_node

    def factor(self):
        """Parse a factor."""
        print(f"Parsing factor. Current token: {self.current_token}")
        if self.current_token:
            token_value, token_type = self.current_token
            if token_type == "NUMBER":
                return self.match("NUMBER")
            elif token_type == "IDENTIFIER":
                return self.match("IDENTIFIER")
            elif token_value == "(":
                self.match("(")
                expr_node = self.exp()
                self.match(")")
                return expr_node
            else:
                self.error("Invalid factor")
        self.error("Invalid factor")









