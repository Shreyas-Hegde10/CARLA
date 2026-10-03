"""
Attaches several of CARLA's sensor types to your already-spawned vehicle
and prints each one's raw output as it arrives, so you can see exactly
what data format each sensor actually produces.

Sensors covered here:
  - sensor.other.lane_invasion   (event: fires when a lane line is crossed)
  - sensor.other.collision       (event: fires on any collision)
  - sensor.other.gnss            (continuous: lat/lon/alt, like a real GPS)
  - sensor.other.imu             (continuous: accelerometer + gyroscope)
  - sensor.camera.semantic_segmentation  (continuous: labeled image,
    each pixel tagged with a class id)

Requires: pip3 install carla==0.9.16 numpy
Run on your laptop with the SSH tunnel open, after a vehicle is already
spawned (e.g. via carla_camera_view.py).
"""

import carla
import numpy as np
import time

def main():
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    world = client.get_world()
    blueprint_library = world.get_blueprint_library()

    vehicles = world.get_actors().filter('vehicle.*')
    if not vehicles:
        raise RuntimeError("No vehicle found. Spawn one first (e.g. run carla_camera_view.py).")
    vehicle = vehicles[0]
    print(f"Attaching sensors to: {vehicle.type_id} (id={vehicle.id})\n")

    actors_to_cleanup = []

    # Lane invasion sensor: fires when crossing a line
    lane_bp = blueprint_library.find('sensor.other.lane_invasion')
    lane_sensor = world.spawn_actor(lane_bp, carla.Transform(), attach_to=vehicle)
    actors_to_cleanup.append(lane_sensor)

    def on_lane_invasion(event):
        crossed_types = [str(marking.type) for marking in event.crossed_lane_markings] #Indicates which type of lane marking was crossed 
        print(f"[LANE INVASION] frame={event.frame} crossed: {crossed_types}")

    lane_sensor.listen(on_lane_invasion)

    #Collision sensor: fires when vehicle collides against something in the map
    collision_bp = blueprint_library.find('sensor.other.collision')
    collision_sensor = world.spawn_actor(collision_bp, carla.Transform(), attach_to=vehicle)
    actors_to_cleanup.append(collision_sensor)

    def on_collision(event):
        impulse = event.normal_impulse #returns a 3-dimensional vector; will need to obtain the magnitude of the vector for overall impulse readings 
        impulse_magnitude = (impulse.x**2 + impulse.y**2 + impulse.z**2) ** 0.5 # Magnitude calculation(Euclidean norm formula)
        print(f"[COLLISION] frame={event.frame} with {event.other_actor.type_id}, impulse=({impulse.x:.2f},{impulse.y:.2f},{impulse.z:.2f})magnitude={impulse_magnitude:.1f}")

    collision_sensor.listen(on_collision)

    # GNSS sensor: continuous, like a real GPS
    gnss_bp = blueprint_library.find('sensor.other.gnss')
    gnss_sensor = world.spawn_actor(gnss_bp, carla.Transform(), attach_to=vehicle)
    actors_to_cleanup.append(gnss_sensor)

    def on_gnss(data):
        print(f"[GNSS] frame={data.frame} lat={data.latitude:.6f} lon={data.longitude:.6f} alt={data.altitude:.2f}")

    gnss_sensor.listen(on_gnss)

    # IMU sensor: accelerometer(linear acceleration) + gyroscope(angular velocity) + compass(orientation with regard to the North in Unreal Engine
    imu_bp = blueprint_library.find('sensor.other.imu')
    imu_sensor = world.spawn_actor(imu_bp, carla.Transform(), attach_to=vehicle)
    actors_to_cleanup.append(imu_sensor)

    def on_imu(data):
        acc = data.accelerometer
        gyro = data.gyroscope
	acc_magnitude 
        print(f"[IMU] frame={data.frame} accel=({acc.x:.2f},{acc.y:.2f},{acc.z:.2f}) "
              f"gyro=({gyro.x:.2f},{gyro.y:.2f},{gyro.z:.2f}) compass={data.compass:.2f}")

    imu_sensor.listen(on_imu)

    # Semantic segmentation camera: continuous, labeled image
    semseg_bp = blueprint_library.find('sensor.camera.semantic_segmentation')
    semseg_bp.set_attribute('image_size_x', '400')
    semseg_bp.set_attribute('image_size_y', '300')
    semseg_transform = carla.Transform(carla.Location(x=1.5, z=2.4))
    semseg_sensor = world.spawn_actor(semseg_bp, semseg_transform, attach_to=vehicle)
    actors_to_cleanup.append(semseg_sensor)

    def on_semseg(image):
        # Each pixel's RED channel holds the semantic class id
        array = np.frombuffer(image.raw_data, dtype=np.uint8)
        array = array.reshape((image.height, image.width, 4))
        class_ids = array[:, :, 2]  # CARLA packs class id in the R channel (BGRA order -> index 2)
        unique_classes = np.unique(class_ids)
        print(f"[SEMSEG] frame={image.frame} classes present in view: {list(unique_classes)}")

    semseg_sensor.listen(on_semseg)

    print("Listening to all sensors. Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nCleaning up sensors...")
        for actor in actors_to_cleanup:
            actor.stop()
            actor.destroy()
        print("Done.")


if __name__ == '__main__':
    main()
