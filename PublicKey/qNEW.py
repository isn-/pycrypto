#
#   qNEW.py : The q-NEW signature algorithm.
# 
#  Part of the Python Cryptography Toolkit, version 1.1
# 
# Distribute and use freely; there are no restrictions on further 
# dissemination and usage except those imposed by the laws of your 
# country of residence.    This software is provided "as is" without
# warranty of fitness for use or suitability for any purpose, express
# or implied. Use at your own risk or not at all. 
# 

import pubkey
from Crypto.Util.number import *
import Crypto.Hash.SHA

error = 'qNEW module'
HASHBITS = 160   # Size of SHA digests

# Generate an qNEW key with N bits
def generate(bits, randfunc, progress_func=None):
    obj=qNEWobj()

    # Generate prime numbers p and q.  q is a 160-bit prime
    # number.  p is another prime number (the modulus) whose bit
    # size is chosen by the caller, and is generated so that p-1
    # is a multiple of q.  
    #
    # Note that only a single seed is used to
    # generate p and q; if someone generates a key for you, you can
    # use the seed to duplicate the key generation.  This can
    # protect you from someone generating values of p,q that have
    # some special form that's easy to break.
    if progress_func: progress_func('p,q\n')
    while (1):
	obj.q = getPrime(160, randfunc)
	#	    assert pow(2, 159L)<obj.q<pow(2, 160L)
	obj.seed = S = longtobytes(obj.q)
	C, N, V = 0, 2, {}
	# Compute b and n such that bits-1 = b + n*HASHBITS
	n= (bits-1) / HASHBITS
	b= (bits-1) % HASHBITS ; powb=pow(long(2), b)
	powL1=pow(long(2), bits-1)
	while C<4096:
	    # The V array will contain (bits-1) bits of random
	    # data, that are assembled to produce a candidate
	    # value for p.
	    for k in range(0, n+1):
		V[k]=bytestolong(Crypto.Hash.SHA.new(S+str(N)+str(k)).digest())
	    p = V[n] % powb
	    for k in range(n-1, -1, -1): 
		p= (p << long(HASHBITS) )+V[k]
	    p = p+powL1		# Ensure the high bit is set

	    # Ensure that p-1 is a multiple of q 
	    p = p - (p % (2*obj.q)-1)

	    # If p is still the right size, and it's prime, we're done!
	    if powL1<=p and isPrime(p): break

	    # Otherwise, increment the counter and try again
	    C, N = C+1, N+n+1
	if C<4096: break   # Ended early, so exit the while loop
	if progress_func: progress_func('4096 values of p tried\n')

    obj.p = p
    power=(p-1)/obj.q

    # Next parameter: g = h**((p-1)/q) mod p, such that h is any 
    # number <p-1, and g>1.  g is kept; h can be discarded.
    if progress_func: progress_func('h,g\n')
    while (1):
	h=bytestolong(randfunc(bits)) % (p-1)
	g=pow(h, power, p)
	if 1<h<p-1 and g>1: break
    obj.g=g

    # x is the private key information, and is 
    # just a random number between 0 and q.
    # y=g**x mod p, and is part of the public information.
    if progress_func: progress_func('x,y\n')
    while (1):
	x=bytestolong(randfunc(20))
	if 0<x<obj.q: break
    obj.x, obj.y=x, pow(g, x, p)

    return obj

# Construct an qNEW object
def construct(tuple):
    obj=qNEWobj()
    if len(tuple) not in [4,5]:
        raise error, 'argument for construct() wrong length' 
    for i in range(len(tuple)):
	field = obj.keydata[i]
	setattr(obj, field, tuple[i])
    return obj

class qNEWobj(pubkey.pubkey):
    keydata=['p', 'q', 'g', 'y', 'x']

    def _sign(self, M, K=''):
	if (self.q<=K):
	    raise error, 'K is greater than q'
	if M<0: 
	    raise error, 'Illegal value of M (<0)'
	if M>=pow(2,161L): 
	    raise error, 'Illegal value of M (too large)'
        r=pow(self.g, K, self.p) % self.q
        s=(K- (r*M*self.x % self.q)) % self.q
        return (r,s)
    def _verify(self, M, sig):
        r, s = sig
	if r<=0 or r>=self.q or s<=0 or s>=self.q: return 0
 	if M<0: 
 	    raise error, 'Illegal value of M (<0)'
	if M<=0 or M>=pow(2,161L): return 0
        v1=pow(self.g, s, self.p)
	v2=pow(self.y, M*r, self.p)
	v=((v1*v2) % self.p)
	v=v % self.q
        if v==r: return 1
        return 0

    def size(self):
	"Return the maximum number of bits that can be handled by this key."
        return 160

    def hasprivate(self):
	"""Return a Boolean denoting whether the object contains
	private components."""
	return hasattr(self, 'x')

    def cansign(self):
	"""Return a Boolean value recording whether this algorithm can generate signatures."""
	return 1
    def canencrypt(self):
	"""Return a Boolean value recording whether this algorithm can encrypt data."""
	return 0
	
    def publickey(self):
	"""Return a new key object containing only the public information."""
        return construct((self.p, self.q, self.g, self.y))
	
object = qNEWobj
