# Mehul Gupta and Turner Edwards
import cozmo
import math
import sys
import time
import random as rand

from cozmo.util import distance_mm, speed_mmps, radians

from cmap import *
from gui import *
from utils import *

MAX_NODES = 20000


def step_from_to(node0, node1, limit=75):
    ########################################################################
    # 1. If distance between two nodes is less than limit, return node1
    # 2. Otherwise, return a node in the direction from node0 to node1 whose
    #    distance to node0 is limit. Recall that each iteration we can move
    #    limit units at most
    # 3. Hint: please consider using np.arctan2 function to get vector angle
    # 4. Note: remember always return a Node object
    distance = get_dist(node0, node1)
    if distance <= limit:
        return node1
    angle = math.atan2(node1.y - node0.y, node1.x - node0.x)
    new_x = node0.x + limit * math.cos(angle)
    new_y = node0.y + limit * math.sin(angle)
    '''
    new_x = node0.x + (node1.x - node0.x) * distance / limit
    new_y = node0.y + (node1.y - node0.y) * distance / limit
    '''
    new_node = Node((new_x, new_y))
    return new_node

    ############################################################################


def node_generator(cmap):
    rand_node = None
    ############################################################################
    # 1. Use CozMap width and height to get a uniformly distributed random node
    # 2. Use CozMap.is_inbound and CozMap.is_inside_obstacles to determine the
    #    legitimacy of the random node.
    # 3. Note: remember always return a Node object
    
    
    # temporary cod below to be replaced
    if rand.random() < .05:
        rand_node = Node(rand.choice(cmap.get_goals()).coord)
    else:
        keep_search = True
        while keep_search:
            x = rand.randrange(0, cmap.width)
            y = rand.randrange(0, cmap.height)
            rand_node = Node((x, y))
            keep_search = cmap.is_inside_obstacles(rand_node)
    return rand_node
    ############################################################################


def RRT(cmap, start):
    cmap.add_node(start)
    map_width, map_height = cmap.get_size()
    while (cmap.get_num_nodes() < MAX_NODES):
        ########################################################################
        # 1. Use CozMap.get_random_valid_node() to get a random node. This
        #    function will internally call the node_generator above
        # 2. Get the nearest node to the random node from RRT
        # 3. Limit the distance RRT can move
        # 4. Add one path from nearest node to random node
        #
        
        
        #temporary code below to be replaced
        rand_node = cmap.get_random_valid_node()
        nearest_node = start
        min_distance = map_height * map_width

        for node in cmap.get_nodes():
            new_distance = get_dist(rand_node, node)
            if new_distance < min_distance:
                min_distance = new_distance
                nearest_node = node

        rand_node = step_from_to(nearest_node, rand_node)
        if not (cmap.is_inside_obstacles(rand_node) or not cmap.is_inbound(rand_node)):
            # cmap.add_node(rand_node)
            ########################################################################
            time.sleep(0.01)
            cmap.add_path(nearest_node, rand_node)

            if cmap.is_solved():
                break


    path = cmap.get_path()
    smoothed_path = cmap.get_smooth_path()

    if cmap.is_solution_valid():
        print("A valid solution has been found :-) ")
        print("Nodes created: ", cmap.get_num_nodes())
        print("Path length: ", len(path))
        print("Smoothed path length: ", len(smoothed_path))
    else:
        print("Please try again :-(")


def CozmoPlanning(robot: cozmo.robot.Robot):
    # Allows access to map and stopevent, which can be used to see if the GUI
    # has been closed by checking stopevent.is_set()
    global cmap, stopevent
    ########################################################################
    # TODO: please enter your code below.
    # Description of function provided in instructions. Potential pseudcode is below

    #assume start position is in cmap and was loaded from emptygrid.json as [50, 35] already
    #assume start angle is 0
    #Add final position as goal point to cmap, with final position being defined as a point that is at the center of the arena 
    #you can get map width and map weight from cmap.get_size()
    dim = cmap.get_size()
    dimWidth = dim[0] / 2
    dimHeight = dim[1] / 2
    cmap.add_goal(Node((dimWidth, dimHeight)))
    #reset the current stored paths in cmap
    #call the RRT function using your cmap as input, and RRT will update cmap with a new path to the target from the start position
    #get path from the cmap
    cmap.reset_paths()
    RRT(cmap, cmap.get_start())
    path = cmap.get_smooth_path()
    
    #marked and update_cmap are both outputted from detect _cube_and_update_cmap(robot, marked, cozmo_pos).
    #and marked is an input to the function, indicating which cubes are already marked
    #So initialize "marked" to be an empty dictionary and "update_cmap" = False
    marked = {}
    update_cmap = False
    curr_index = 0
    prev_angle = 0
    #while the current cosmo position is not at the goal:
    while not path == None and (robot.pose.position.x != cmap.get_goals()[0].x and robot.pose.position.y != cmap.get_goals()[0].y)\
            and not curr_index >= len(path)-1:

        current_node = path[curr_index]
        curr_index += 1

        #break if path is none or empty, indicating no path was found

        # Get the next node from the path
        #drive the robot to next node in path. #First turn to the appropriate angle, and then move to it
        #you can calculate the angle to turn through a trigonometric function
        next_node = path[curr_index]

        next_angle = math.atan2(next_node.y - current_node.y, next_node.x - current_node.x)
        diff_angle = math.atan2(math.sin(next_angle - prev_angle), math.cos(next_angle - prev_angle))

        robot.turn_in_place(radians(diff_angle)).wait_for_completed()
        driveDistance = get_dist(current_node, next_node)
        robot.drive_straight(distance_mm(driveDistance), speed_mmps(50)).wait_for_completed()

        # Update the current Cozmo position (cozmo_pos and cozmo_angle) to be new node position and angle 
        prev_angle = next_angle
        cozmo_pos = next_node

        # Set new start position for replanning with RRT

        # detect any visible obstacle cubes and update cmap
        cubes_placed = detect_cube_and_update_cmap(robot, marked, cozmo_pos)
        
        #if we detected a cube, indicated by update_cmap, reset the cmap path, recalculate RRT, and get new paths
        if cubes_placed[0]:
            cmap.reset_paths()
            RRT(cmap, next_node)
            path = cmap.get_smooth_path()
            curr_index = 0
        ########################################################################

def get_global_node(local_angle, local_origin, node):
    """Helper function: Transform the node's position (x,y) from local coordinate frame specified by local_origin and local_angle to global coordinate frame.
                        This function is used in detect_cube_and_update_cmap()
        Arguments:
        local_angle, local_origin -- specify local coordinate frame's origin in global coordinate frame
        local_angle -- a single angle value
        local_origin -- a Node object
        Outputs:
        new_node -- a Node object that decribes the node's position in global coordinate frame
    """
    ########################################################################
    a = np.array([[math.cos(local_angle), -math.sin(local_angle), local_origin[0]],
                    [math.sin(local_angle), math.cos(local_angle), local_origin[1]],
                    [0, 0, 1]])

    b = np.array([[node[0]], [node[1]], [1]])
    b.reshape((3, 1))
    new_node_mat = a @ b
    new_node = Node((new_node_mat[0][0], new_node_mat[1][0]))
    return new_node
    ########################################################################


def detect_cube_and_update_cmap(robot, marked, cozmo_pos):
    """Helper function used to detect obstacle cubes and the goal cube.
       1. When a valid goal cube is detected, old goals in cmap will be cleared and a new goal corresponding to the approach position of the cube will be added.
       2. Approach position is used because we don't want the robot to drive to the center position of the goal cube.
       3. The center position of the goal cube will be returned as goal_center.

        Arguments:
        robot -- provides the robot's pose in G_Robot
                 robot.pose is the robot's pose in the global coordinate frame that the robot initialized (G_Robot)
                 also provides light cubes
        cozmo_pose -- provides the robot's pose in G_Arena
                 cozmo_pose is the robot's pose in the global coordinate we created (G_Arena)
        marked -- a dictionary of detected and tracked cubes (goal cube not valid will not be added to this list)

        Outputs:
        update_cmap -- when a new obstacle or a new valid goal is detected, update_cmap will set to True
        goal_center -- when a new valid goal is added, the center of the goal cube will be returned
    """
    global cmap

    # Padding of objects and the robot for C-Space
    cube_padding = 60.
    cozmo_padding = 100.

    # Flags
    update_cmap = False
    goal_center = None

    # Time for the robot to detect visible cubes
    time.sleep(1)

    for obj in robot.world.visible_objects:

        if obj.object_id in marked:
            continue

        # Calculate the object pose in G_Arena
        # obj.pose is the object's pose in G_Robot
        # We need the object's pose in G_Arena (object_pos, object_angle)
        dx = obj.pose.position.x - robot.pose.position.x
        dy = obj.pose.position.y - robot.pose.position.y

        object_pos = Node((cozmo_pos.x+dx, cozmo_pos.y+dy))
        object_angle = obj.pose.rotation.angle_z.radians

        # Define an obstacle by its four corners in clockwise order
        obstacle_nodes = []
        obstacle_nodes.append(get_global_node(object_angle, object_pos, Node((cube_padding, cube_padding))))
        obstacle_nodes.append(get_global_node(object_angle, object_pos, Node((cube_padding, -cube_padding))))
        obstacle_nodes.append(get_global_node(object_angle, object_pos, Node((-cube_padding, -cube_padding))))
        obstacle_nodes.append(get_global_node(object_angle, object_pos, Node((-cube_padding, cube_padding))))
        cmap.add_obstacle(obstacle_nodes)
        marked[obj.object_id] = obj
        update_cmap = True

    return update_cmap, goal_center, marked


class RobotThread(threading.Thread):
    """Thread to run cozmo code separate from main thread
    """

    def __init__(self):
        threading.Thread.__init__(self, daemon=True)

    def run(self):
        # Please refrain from enabling use_viewer since it uses tk, which must be in main thread
        cozmo.run_program(CozmoPlanning,use_3d_viewer=False, use_viewer=False)
        stopevent.set()


class RRTThread(threading.Thread):
    """Thread to run RRT separate from main thread
    """

    def __init__(self):
        threading.Thread.__init__(self, daemon=True)

    def run(self):
        while not stopevent.is_set():
            RRT(cmap, cmap.get_start())
            time.sleep(100)
            cmap.reset_paths()
        stopevent.set()


if __name__ == '__main__':
    global cmap, stopevent
    stopevent = threading.Event()
    robotFlag = False
    for i in range(0,len(sys.argv)): #reads input whether we are running the robot version or not
        if sys.argv[i] == "-robot":
            robotFlag = True
    if (robotFlag):
        #creates cmap based on empty grid json
        #"start": [50, 35],
        #"goals": [] This is empty
        cmap = CozMap("maps/emptygrid.json", node_generator) 
        robot_thread = RobotThread()
        robot_thread.start()
    else:
        cmap = CozMap("maps/map6.json", node_generator)
        sim = RRTThread()
        sim.start()
    visualizer = Visualizer(cmap)
    visualizer.start()
    stopevent.set()
