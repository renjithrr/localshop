class Kw:
    def __init__(self, label=None, **kwargs):
        assert (len(kwargs) == 1)
        for k, v in kwargs.items():
            self.id = k
            self.v = v
        self.label = label or self.id


class Konstants:
    def __init__(self, *args):
        self.klist = args
        for k in self.klist:
            setattr(self, k.id, k.v)

    def choices(self):
        return [(k.v, k.label) for k in self.klist]




import math, random

def OTPgenerator() :
	digits_in_otp = "0123456789"
	OTP = ""

# for a 4 digit OTP we are using 4 in range
	for i in range(4) :
		OTP += digits_in_otp[math.floor(random.random() * 10)]

	return OTP
