class TrieNode:
    """A node in the Trie structure."""
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.word = None

class Trie:
    """Trie data structure for efficient prefix searching."""
    def __init__(self):
        """Initializes the Trie with a root node."""
        self.root = TrieNode()

    def insert(self, word: str):
        """Inserts a word into the trie, character by character."""
        node = self.root
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
        node.word = word

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
                return []
            node = node.children[char]
        
        suggestions = []
        self._find_all_from_node(node, suggestions)
        return suggestions