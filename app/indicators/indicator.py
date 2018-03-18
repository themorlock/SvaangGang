
class Indicator:
	def __init__(self, utils, config):
		self._utils = utils
		self._conf = config

	async def analyze(self):
		raise NotImplementedError("Please implement this method u.u")
