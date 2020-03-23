# A Different CSS - Crypto - 400 points - 4 solves
> _This challenge was created by our sponsor, [ZeroDays](https://zerodays.ie)!_
> 
> I long for the good old days, when children obeyed their parents, ignorance was
> bliss and the DVD's were still encrypted.
> 
> We've taken some inspiration from the DVD CSS encryption scheme for this
> challenge. Can you crack our custom scheme and recover the flag?
> 
> Hint: these slides may help:
> http://www.ccs.neu.edu/home/alina/classes/Spring2018/Lecture5.pdf

## Files:
- [enc.py](enc.py)
- [enc.log](enc.log)

The encryption used in enc.py uses two [LFSR](https://en.wikipedia.org/wiki/Linear-feedback_shift_register) keystreams, which are known for their weak cryptographic resiliance. Assuming we know the first k bits of an k-bit LFSR keystream we can calculate the rest of the bits using that info. Specifically those k bits are actually the initial state of the LFSR. 

The problem is that this encryption uses not one LFSR keystream but two! Luckily the hint references a presentation talking about this exact kind of encryption, and a way of cracking it (page 12). So really this challenge is just a matter of implementing the algorithm described in the slides.

The steps are as follows: For all possible initial states of the smaller LFSR:
- Get the first 20 bytes of the smaller LFSR. (To speed it up a bit I just used 10 and it worked)
- Find the bytes of the larger LFSR that would result in the encoded output.
- Take the first 19 bits as your state for the larger LFSR
- Check if decryption results in the correct prefix
- If so you found the state, decrypt the rest of the data to print your flag

All this is implemented in [dec.py](dec.py) it takes a bit of time to run since python is slow, but I didn't want to have to rewrite the LFSR code.

```
$ python3 dec.py 
Progress: [======================        ] 73.85
state1 =  [1 0 1 1 1 1 1 0 0 0 0 0 0]
state2 =  [0 1 1 1 1 1 1 0 0 0 0 1 1 1 1 0 1 1 0]
bytearray(b'Well done! You got the flag. The flag is HackTrinity{n0t_htm1_cs5_but_dvd_css}')
```