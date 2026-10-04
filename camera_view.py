"""
Spawns a vehicle in CARLA, attaches an RGB camera, and displays the live
feed in a window on your laptop. Press 'q' in the image window to quit
and clean up.

Requires: pip3 install carla==0.9.16 opencv-python numpy
Run this on your laptop, with the SSH tunnel (port 2000/2001) already open.
"""

import carla
import numpy as np
import cv2
import random
import queue  
import math


def lateral_offset(vehicle_transform, waypoint_transform): 
        """
        Returns signed lateral distance(in metres) from the vehicle's position to 
        the waypoint's centerline, using a vector perpendicular to the lane to determine 
        the sign 

        Positive: vehicle is right of centre 
        Negative: vehicle is left of centre
        """ 

        vehicle_location = vehicle_transform.location #3D vector of distance from vehicle origin to a spot in metres 
        waypoint_location = waypoint_transform.location 

        dx = vehicle_location.x - waypoint_location.x 
        dy = vehicle_location.y - waypoint_location.y

        yaw_rad = math.radians(waypoint_transform.rotation.yaw)
        right_x = math.cos(yaw_rad + math.radians(90))
        right_y = math.sin(yaw_rad + math.radians(90)) 

        return dx * right_x + dy * right_y 
        

def main():
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0) # Sets the amount of time that a network call is allowed to execute; if it exceeds said value, an exception is raised 
    world = client.get_world() 
    carla_map = world.get_map()

    blueprint_library = world.get_blueprint_library()
    vehicle_bp = blueprint_library.find('vehicle.audi.etron') 
    spawn_points = world.get_map().get_spawn_points()
    spawn_point = random.choice(spawn_points)

    vehicle = world.spawn_actor(vehicle_bp, spawn_point)
    print(f"Spawned {vehicle_bp.id} at {spawn_point.location}")

    vehicle.set_autopilot(False) 
    Kp = 0.5 # Proportional gain constant for steering control 

    # Attach an RGB camera facing forward, mounted like a dashcam.
    camera_bp = blueprint_library.find('sensor.camera.rgb')
    camera_bp.set_attribute('image_size_x', '800')
    camera_bp.set_attribute('image_size_y', '600')
    camera_bp.set_attribute('fov', '90')
    camera_transform = carla.Transform(
	carla.Location(x=-6.5, z=3.0), 
        carla.Rotation(pitch=-15.0)
    )

    camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)

    image_queue = queue.Queue()
    camera.listen(image_queue.put)

    print("Streaming camera feed. Press 'q' in the image window to quit.")

    frame_count = 0 

    try:
        while True:
            image = image_queue.get() # CARLA represents images with 32-bit BGRA colours
            array = np.frombuffer(image.raw_data, dtype=np.uint8) #image.raw_data is a flattened array of that image
            array = array.reshape((image.height, image.width, 4))  # BGRA
            frame = array[:, :, :3]  # drop alpha channel since cv2.imshow expects only 3 channels(R,G,B)

            # get lateral offset per frame
            vehicle_transform = vehicle.get_transform 
            waypoint_transform = carla_map.get_waypoint(vehicle_transform.location,project_to_road=True, lane_type=carla.LaneType.Driving).transform 
            offset = lateral_offset(vehicle_transform, waypoint_transform) 

            steer = -Kp * offset 
            steer = max(-1.0, min(1.0, steer)) # clamp to [-1, 1] range 
            

            frame_count +=1 
            if frame_count % 10 == 0: 
                print(f"Lateral offset from lane center: {offset:.2f} m")

            vehicle.apply_control(carla.VehicleControl(throttle=0.3, steer=steer)) 

            cv2.imshow('CARLA Camera', frame)

            #cv2.waitKey(1) returns the character code of the currently pressed key. In some operating systems, 
	        #cv2.waitKey(1) returns more than one byte for the character code, which doesn't allow for comparison with 
            # ord('q'), which returns a single byte representation(ASCII) of the key. Thus, the boolean flag 0xFF is
	        # used to ensure that only the last byte is extracted from the result of cv2.waitKey(1)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        print("Cleaning up actors...")
        camera.stop()
        camera.destroy()
        vehicle.destroy()
        cv2.destroyAllWindows()
        print("Done.")

if __name__ == '__main__':
    main()
