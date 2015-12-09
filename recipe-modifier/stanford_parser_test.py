import os
import re

class Node(object):
	def __init__(self, data):
		self.data = data
		self.left = None
		self.right = None
		self.parent = None

def add_child(node_list, parent, symbol, leaf_status):
	child = Node(symbol)
	child.parent = parent
	if (parent):
		if (parent.left==None):
			parent.left = child
		else:
			parent.right = child
	else:
		root = child
	if (leaf_status):
		node_list.append(child)
	return child

# return true if symbol is not a parenthesis or separator
def is_tag(symbol):
	if (symbol in [")", "("] or str(symbol).isspace() or str(symbol)==""):
		return False
	return True

# Define segments according to rules
def is_coordinating_conjunction(word):
	if (word.parent.data == "CC"):
		if (word.parent.parent and word.parent.parent.data not in ["NP", "PP", "ADJP"]):
			return True
	return False

def is_comma_condition(word):
	if (word.data=="," and word.parent.parent):
		if (word.parent.parent.data not in ["NP", "PP", "ADJP"]):
			return True

def is_break_symbol(word):
	if (word.data in [".", ":", ";", "!"]):
		return True
	return False

def splitParserOutput(parser_out):
    current_recipe_name = []
    current_recipe_text = []
    current_recipe_reviews = [[]]
    state = 'title'
    for phrase in parser_out:
        if '<RECIPE_BREAK>' in phrase:
            yield current_recipe_name, current_recipe_text, current_recipe_reviews
            state = 'title'
            current_recipe_name = []
            current_recipe_text = []
            current_recipe_reviews = [[]]
        elif '<RECIPE_TITLE_BREAK>' in phrase:
            state = 'text'
            current_recipe_name = ''.join(current_recipe_name)
        elif '<RECIPE_TEXT_BREAK>' in phrase:
            state = 'review'
        elif '<RECIPE_REVIEW_BREAK>' in phrase:
            current_recipe_reviews.append([])
        else:
            if state == 'title':
                current_recipe_name.append(phrase)
            elif state == 'text':
                current_recipe_text.append(phrase)
            elif state == 'review':
                current_recipe_reviews[-1].append(phrase)
            else:
                raise ValueError, 'shouldnt get here'

def parse(txt_file, output_file):
    parser_out = os.popen("../stanford-parser-2012-11-12/lexparser.sh %s" % txt_file).readlines()
    parsed = {}
    i = 0
    for recipe_name, recipe_text, reviews in splitParserOutput(parser_out):
        parsed[recipe_name] = {'instructions':parseParagraph(recipe_text),
                                'reviews':[]}
        for review in reviews:
            parsed[recipe_name]['reviews'].append(parseParagraph(review))
        if i%100 == 0:
            with open(output_file, 'wb') as f:
                pickle.dump(parsed, f)
        i+=1

def parseParagraph(paragraph):
    bracketed_parse = " ".join( [i.strip() for i in paragraph if len(i.strip()) > 0 and i.strip()[0] == "("])

    #print bracketed_parse

    # Split the parse into an array
    split =  re.split('(\W)', bracketed_parse)
    #print split

    # We will store the leaf nodes here in the correct order
    node_list = []
    current_parent = None
    current_node = None
    root = None
    last_symbol = None # Store the last symbol we've seen to identify the leaf nodes

    # Go through the array and build the tree
    # The leaf node's type is stored as its PARENT
    for symbol in split:
        if (str(symbol).isspace() or str(symbol)==""):
            pass
        else:
            if (symbol=="("):
                if (last_symbol!=")"):
                    current_parent = current_node
            elif (symbol==")"):
                current_parent = current_parent.parent
            elif (is_tag(last_symbol)): # Leaf node case
                current_parent = current_node
                child = add_child(node_list, current_parent, symbol, True)
                current_node = child
            else:
                child = add_child(node_list, current_parent, symbol, False)
                current_node = child
            last_symbol = symbol

    # Now just segment based on the rules and print the segments
    all_segments = []

    current_segment = []
    for i in range(len(node_list)):
        word= node_list[i]
        current_segment.append(word.data)
        #print "word data: " + word.data

        # Hack to get the spacing correct before punctuation
        if (is_break_symbol(word) or is_comma_condition(word)):
            joined_str = ' '.join(current_segment[:-1])
            #print joined_str + current_segment[-1]
            all_segments.append(joined_str+ current_segment[-1])
            current_segment = []
        if (is_coordinating_conjunction(word)): #sentence break
            #print ' '.join(current_segment)
            all_segments.append(' '.join(current_segment))
            current_segment = []
    if len(' '.join(current_segment))>0:
        all_segments.append(' '.join(current_segment))
        #print ' '.join(current_segment)
    #print all_segments
    return all_segments
