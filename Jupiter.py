import sys
import base64
from PIL import Image

strWelcome = '''\
Welcome to Jupiter!

* Jupiter is an easy-to-use tool for image digital watermarking.
It will help you have specific watermarker(text or image) embedded into or
extracted from your image file with least damage made to the visual quality.

* Author: Lifu Huang
* Version: 0.1
'''
strHelp = '''
* Command:
>>> image in   -- Embed graphical watermarker into an image file
>>> image out  -- Extract graphical watermarker from embedded image file
>>> text in    -- Embed text information into an image file
>>> text out   -- Extract text hidden within an image file
>>> help       -- Show command instruction
>>> exit       -- Exit Jupiter
'''
defaultWaterMarker = ''
defaultPosition = ''
tmpPosition = 'E:\\destination.png'
tmpWatermarker = 'E:\\watermarker.png'

class InputError(Exception):
    '''Unidentifiable user input.'''
    
    pass

class DecryptionError(Exception):
    '''Exception take place in the process of decryption'''

    pass

def progress_bar(cur, tot, width = 32, prompt = '* Progress: '):
    '''Print progress bar onto console.'''
    
    percent = cur / tot
    sys.stdout.write("\r{prmpt}[{bar:{wid}}] {val}%".format(prmpt = prompt, bar = '=' * int(percent * width), val = int(percent * 100), wid = width))
    sys.stdout.flush()
    

def print_welcome():
    '''Print welcome message in the console.'''
    
    print(strWelcome)
    print()
    print(strHelp)

def embedImage(sourceFile, destFile, watermarkerFile):
    '''Embed watermarker into an image file.'''
    
    print('* Loading source file {}...'.format(sourceFile))
    print('* Loading watermarker file {}...'.format(watermarkerFile))
    with Image.open(sourceFile) as image, Image.open(watermarkerFile) as watermarker:
        if image.mode != 'RGB':
            print('* Converting source image to RGB image...')
            image = image.convert('RGB')
        if watermarker.mode != '1':
            if input('Warning: Watermarker provided is not binary-value pixel file.\
                     Extra information will be lost. Do you want to continue(y/n)?') != 'y':
                return
            print('* Converting watermarker to binary-value image...')
            watermarker = watermarker.convert('1')
        if watermarker.size != image.size:
            print('* Resizing watermarker...')
            watermarker = watermarker.resize(image.size)
        #watermarker.show()
        print('* Processing image...')
        for x in range(image.size[0]):
            for y in range(image.size[1]):
                pixel = image.getpixel((x, y))
                info = watermarker.getpixel((x, y))
                image.putpixel((x, y), ((pixel[0] & ((1 << 8) - 2)) | (1 if info == 255 else 0), pixel[1], pixel[2]))
            progress_bar(x+1, image.size[0])
        print()
        #image.show()
        print('* Saving watermarked image to {}...'.format(destFile))
        image.save(destFile)
    print('* Done!')
    return
    
def extractImage(sourceFile, watermarkerFile):
    '''Extract watermarker from image file.'''
    
    print('* Loading source file {}...'.format(sourceFile))
    with Image.open(sourceFile) as image:
        print('* Creating watermarker...')
        watermarker = Image.new('1', image.size);
        print('* Processing image...')
        for x in range(image.size[0]):
            for y in range(image.size[1]):
                pixel = image.getpixel((x, y))
                watermarker.putpixel((x, y), 255 if (pixel[0] & 1) == 1 else 0)
            progress_bar(x+1, image.size[0])
        print()
        print('* Saving extracted watermarker to {}...'.format(watermarkerFile))
        #watermarker.show()
        watermarker.save(watermarkerFile)
    print('* Done!')
    return

def encrypt(text, key):
    '''Encrypt text with key.'''

    if key == '':
        return text
    else:
        tmp = bytearray()
        #insert 'Correct' in the front as check code
        codeText = ('Correct' + text).encode('utf-8')
        codeKey = key.encode('utf-8')
        for idx in range(len(codeText)):
            tmp.append(codeText[idx] ^ codeKey[idx % len(codeKey)])
        return base64.b64encode(tmp).decode('utf-8')


def decrypt(text, key):
    '''Decrypt text with key.'''

    if key == '':
        return text
    else:
        try:
            tmp = bytearray()
            codeText = base64.b64decode(text.encode('utf-8'))
            codeKey = key.encode('utf-8')
            for idx in range(len(codeText)):
                tmp.append(codeText[idx] ^ codeKey[idx % len(codeKey)])
            result = bytes(tmp).decode('utf-8')
            #check code test
            if(result[0:7] == 'Correct'):
                return result[7:]
            else:
                raise DecryptionError
        except Exception:
            raise DecryptionError


def embedText(sourceFile, destFile, text):
    '''Embed text into an image file.'''
    
    print('* Loading source file {}...'.format(sourceFile))
    with Image.open(sourceFile) as image:
        if image.mode != 'RGB':
            print('* Converting source image to RGB image...')
            image = image.convert('RGB')
            
        print('* Encoding...')
        code = text.encode('utf-8')
        print('* Checking image size...')
        if len(image.getdata()) // 8 < len(code):
            if input('Warning: Text provided is too long be be hidden thus will be truncated. Do you want to continue(y/n)?') != 'y':
                return
            print('* Truncating text...')
            code = code[0: len(image.getdata()) // 8]
            
        print('* Processing image...')
        result = list()
        for i in range(0, len(code)):
            for j in range(8):
                pixel = image.getdata()[i * 8 + j]
                result.append((pixel[0], (pixel[1] & ((1 << 8) - 2) | (1 if code[i] & (1 << j) else 0)), pixel[2]))
            progress_bar(i+1, len(code))
        print()
        
        print('* Embedding size information...')
        for i in range(32):
            result[i] = (result[i][0], result[i][1], (result[i][2] & ((1 << 8) - 2) | (1 if len(code) & (1 << i) else 0)))
        
        image.putdata(result)
        #image.show()
        print('* Saving result to {}...'.format(destFile))
        image.save(destFile)
    print('* Done!')
    return

def extractText(sourceFile):
    '''Embed text into an image file.'''

    print('* Loading source file {}...'.format(sourceFile))
    with Image.open(sourceFile) as image:
        
        print('* Processing image...')
        data = image.getdata()

        print('* Extracting size information...')
        size = 0
        for i in range(32):
            size |= ((data[i][2] & 1) << i)
        # print('! Size = {}'.format(size))
        seq = []
        for i in range(0, size):
            byte = 0
            for j in range(8):
                byte |= ((data[i * 8 + j][1] & 1) << j)
            seq.append(byte)
            progress_bar(i+1, size)
        print()
        print('* Decoding...')
        res = str(bytes(seq).decode('utf-8'))        
    print('* Done!')
    return res

def main():
    '''Main function invoked in script mode.'''
    
    print_welcome()
    while(True):
        try:
            cmd = input('>>>').strip()
            if cmd == 'image in':
                source = input('Source File Path: ')
                dest = input('Destination File Path: ')
                watermarker = input('Watermarker File Path: ')
                embedImage(source, dest, watermarker)
            elif cmd == 'image out':
                source = input('Source File Path: ')
                dest = input('Destination File Path: ')
                extractImage(source, dest)
            elif cmd == 'text in':
                source = input('Source File Path: ')
                dest = input('Destination File Path: ')
                text = input('Text: ')
                code = input('Code: ')
                encrypted = encrypt(text, code)
                embedText(source, dest, encrypted)
            elif cmd == 'text out':
                source = input('Source File Path: ')
                code = input('Code: ')
                text = decrypt(extractText(source), code)
                print('\nHidden text: ', text, sep = '')
            elif cmd == 'help':
                print(strHelp)
            elif cmd == 'exit':
                sys.exit(0)
            else:
                raise InputError
        except InputError:
            print('Wrong input format, please check the instruction for help.')
        except FileNotFoundError:
            print('File not found, please check your input!')
        except DecryptionError:
            print('Decryption Error! Please make sure that you input the correct code!')
        except Exception as e:
            print('\nUnknown Exception! Please contact the author for help!')
            print(e)
        
def test():
    a = '你好世界！hello World!'
    print(a)
    print(encrypt(a, '12345'))
    print(decrypt(encrypt(a, '12345'),'12345'))
    print(decrypt(encrypt(a, ''), ''))
    
if __name__ == '__main__':
    main()
