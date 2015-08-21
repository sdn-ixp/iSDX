def decompose_verbrokenheimerschnitzel(row_2_cols):
	""" Input is a dictionary with matrix row IDs as keys and a list of each
		row's contents (column indices of nonzero row entries) as a value.
		BROKEN. DONUT USE.
	"""
	item_2_group = {}
	item_buddies = {}
	for group in row_2_cols.values():
		for item in group:
			# if we haven't seen this item before
			if item not in item_2_group:
				# initialize his mapping
				item_2_group[item] = [group]
				# and assume all his neighbors are buddies
				item_buddies[item] = set(group)
			# if we have seen him before
			else:
				# remove any fake buddies
				item_buddies[item].intersection_update(group)
				# update the mapping
				item_2_group[item].append(group)


	for item, buddies in item_buddies.iteritems():
		item_buddies[item] = frozenset(buddies)

	final_sets = {}

	for row, group in row_2_cols.iteritems():
		final_set = set([])
		# add in all the corresponding prefix groups
		for item in group:
			final_set.add(item_buddies[item])

		final_sets[row] = final_set


	return final_sets






def decompose_sequential(col_2_rows):
	""" Input is a dictionary with column IDs as keys and a list of each
		column's contents (row indices of nonzero entries) as a value.

		Input is a dictionary with prefixes as keys and lists of participants
		as values. If a participant A has a route to p1, it will appear as
		'sA' in the value list. If A is the default next-hop to p1, it will
		also appear as 'bA' in the list.

		Example: With participants [A,B,C] and prefixes [p1,p2,p3,p4],
		an input could be {p1:[sA], p2:[sA,sB], p3:[sA,sB], p4:[sB,sC]}

		Output is participant to prefix-group mapping.
		Example: {sA:[[p1], [p2,p3]], sB:[[p2,p3], [p4]], sC:[[p4]]}
	"""

	froset_2_col = {}
	for col_id, col_contents in col_2_rows.iteritems():
		froset = frozenset(col_contents)
		if froset not in froset_2_col:
			froset_2_col[froset] = []
		froset_2_col[froset].append(col_id)



	final_sets = {}
	for froset, cols in froset_2_col.iteritems():
		for row in froset:
			if row not in final_sets:
				final_sets[row] = []
			final_sets[row].append(cols)


	return final_sets






if __name__ == '__main__':	

	groups = {'a':[1,2,3], 'b':[2,3,4], 'c':[4]}

	spuorg = {}
	for key, values in groups.iteritems():
		for item in values:
			if item not in spuorg:
				spuorg[item] = []
			spuorg[item].append(key)

	print groups
	#print spuorg

	print decompose_sequential(spuorg)