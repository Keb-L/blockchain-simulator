import sys, csv

'''
Parse csv files
'''
def get_topology(locations_filename, topology_filename):
    locations = []
    with open(f'{locations_filename}', newline='') as f:
        # ignore first row
        first_row = True
        location_reader = csv.reader(f)
        for row in location_reader:
            try:
                latitude = float(row[1])
                longitude = float(row[2])
                locations.append((latitude, longitude))
            except:
                if first_row: 
                    first_row = False
                    pass
                else:
                    print('Invalid latitude longitude provided')
                    sys.exit()


    num_nodes = len(locations)
    G = []
    with open(f'{topology_filename}', newline='') as f:
        # ignore first row
        first_row = True
        adjacency_reader = csv.reader(f)
        node = 1
        for row in adjacency_reader:
            G.append([])
            for i in range(0, len(row)):
                adjacent = int(row[i])
                if adjacent==1:
                    G[-1].append(i)
    return num_nodes, locations, G
