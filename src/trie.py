class TrieNode:
    """A node in the Trie structure."""
    def __init__(self):
        self.children = {}
        # is_end_of_word is True if the node represents the end of a word
        self.is_end_of_word = False
        # Store the full, original-cased word at the end node for easy retrieval
        self.word = None

class Trie:
    """Trie data structure for efficient prefix searching."""
    def __init__(self):
        """Initializes the Trie with a root node."""
        self.root = TrieNode()

    def insert(self, word: str):
        """Inserts a word into the trie, character by character."""
        node = self.root
        # We store everything in lowercase to make searching case-insensitive
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
        node.word = word # Store the original cased word

    def _find_all_from_node(self, node: TrieNode, suggestions: list):
        """A recursive helper to find all words starting from a given node."""
        if node.is_end_of_word:
            suggestions.append(node.word)
        
        for child_node in node.children.values():
            self._find_all_from_node(child_node, suggestions)

    def search_prefix(self, prefix: str) -> list[str]:
        """Returns all words in the trie that start with the given prefix."""
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return [] # Prefix does not exist
            node = node.children[char]
        
        suggestions = []
        self._find_all_from_node(node, suggestions)
        return suggestions
