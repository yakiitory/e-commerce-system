import json
import argparse
from typing import List, Dict


class TreeNode:
	def add_value(self, value: int):
		self.values.append(value)

	def remove_value(self, value: int):
		if value in self.values:
			self.values.remove(value)

	def set_values(self, values: list):
		self.values = list(values)

	def clear_values(self):
		self.values.clear()
	def __init__(self, name: str):
		self.name = name
		self.children = {}
		self.values = []  # List of integers for each category

	def add_child(self, name: str) -> "TreeNode":
		if name not in self.children:
			self.children[name] = TreeNode(name)
		return self.children[name]

	def to_dict(self):
		result = {}
		if self.children:
			result["children"] = {name: child.to_dict() for name, child in self.children.items()}
		result["values"] = self.values
		return result


class Tree:
	def __init__(self, root_name: str = "Categories"):
		self.root = TreeNode(root_name)

	def add_path(self, path: List[str]):
		node = self.root
		for part in path:
			node = node.add_child(part)

	def to_dict(self):
		return {self.root.name: self.root.to_dict()}

	def to_json(self, **kwargs) -> str:
		return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, **kwargs)

	def ascii_tree(self, include_root: bool = True) -> str:
		lines: List[str] = []

		def _rec(node: TreeNode, prefix: str = ""):
			children = list(node.children.values())
			for i, child in enumerate(children):
				is_last = (i == len(children) - 1)
				branch = "└── " if is_last else "├── "
				# Show values next to child name if any
				value_str = f" {child.values}" if child.values else ""
				lines.append(prefix + branch + child.name + value_str)
				extension = "    " if is_last else "│   "
				_rec(child, prefix + extension)

		if include_root:
			lines.append(self.root.name)
			_rec(self.root)
		else:
			_rec(self.root)

		return "\n".join(lines)


def build_tree_from_categories() -> Tree:
	paths = [
		["Electronics", "Smartphones"],
		["Electronics", "Laptops & Computers"],
		["Electronics", "Cameras & Photography"],
		["Electronics", "Audio & Headphones"],
		["Electronics", "Wearable Technology"],

		["Fashion and Apparel", "Men’s Clothing"],
		["Fashion and Apparel", "Women’s Clothing"],
		["Fashion and Apparel", "Kids’ Clothing"],
		["Fashion and Apparel", "Shoes"],
		["Fashion and Apparel", "Accessories (Bags, Belts, Jewelry)"],

		["Home and Furniture", "Living Room Furniture"],
		["Home and Furniture", "Bedroom Furniture"],
		["Home and Furniture", "Kitchen & Dining"],
		["Home and Furniture", "Home Decor"],
		["Home and Furniture", "Lighting"],

		["Beauty and Personal Care", "Skincare"],
		["Beauty and Personal Care", "Makeup"],
		["Beauty and Personal Care", "Haircare"],
		["Beauty and Personal Care", "Fragrances"],
		["Beauty and Personal Care", "Bath & Body"],

		["Health and Wellness", "Vitamins & Supplements"],
		["Health and Wellness", "Fitness Equipment"],
		["Health and Wellness", "Personal Care Devices"],

		["Nutrition & Diet", "Food and Beverage"],
		["Nutrition & Diet", "Snacks & Sweets"],
		["Nutrition & Diet", "Beverages"],
		["Nutrition & Diet", "Organic & Natural Foods"],
		["Nutrition & Diet", "Gourmet & Specialty Foods"],

		["Toys, Hobby, and DIY", "Action Figures & Collectibles"],
		["Toys, Hobby, and DIY", "Arts & Crafts"],
		["Toys, Hobby, and DIY", "Educational Toys"],
		["Toys, Hobby, and DIY", "Outdoor Play"],
	]

	tree = Tree(root_name="List of Categories in an E-commerce System")
	for p in paths:
		tree.add_path(p)
	return tree


def main():
	tree = build_tree_from_categories()

	def add_values_to_all_children(node):
		for child in node.children.values():
			child.set_values([100, 200])
			add_values_to_all_children(child)

	add_values_to_all_children(tree.root)
	print(tree.ascii_tree(include_root=True))


if _name_ == "_main_":
	main()