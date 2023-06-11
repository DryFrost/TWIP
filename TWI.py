from pydem.pydem.processing_manager import ProcessManager

elevation_source_path = "/home/dryfrost/Desktop/TWI_INPUT"
elevation_target_path = "/home/dryfrost/Desktop/TWI_OUTPUT"

pm = ProcessManager(elevation_source_path,elevation_target_path)

pm.process()
