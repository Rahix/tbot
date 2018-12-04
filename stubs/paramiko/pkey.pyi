import typing

class PKey(object):
	@classmethod
	def from_private_key_file(
		cls,
		filename: typing.Optional[str],
		password: typing.Optional[str]
	) -> "PKey": ...
