import graphviz

# Create a simple tree
dot = graphviz.Digraph()
dot.node('A', 'Root')
dot.node('B', 'Child 1')
dot.node('C', 'Child 2')
dot.edges(['AB', 'AC'])

# Save the tree as a PNG image
dot.render('tree', format='png', cleanup=True)

# # Create a simple tree
# dot = graphviz.Digraph()
# dot.node('A', 'Root')
# dot.node('B', 'Child 1')
# dot.node('C', 'Child 2')
# dot.edges(['AB', 'AC'])

# Save the tree as a PNG image
# dot.render('tree', format='png', cleanup=True)


