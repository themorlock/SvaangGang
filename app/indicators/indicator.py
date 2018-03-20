
class Indicator:
	def __init__(self, utils, config, logger):
		self.utils = utils
		self.conf = config
		self.logger = logger

	async def analyze(self):
		raise NotImplementedError("Please implement this method u.u")
