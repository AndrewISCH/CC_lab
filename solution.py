# coding: utf-8
from Pyro4 import expose
import random
import gc


class Solver:
    def __init__(self, workers=None, input_file_name=None, output_file_name=None):
        self.workers = workers
        self.input_file_name = input_file_name
        self.output_file_name = output_file_name
    
    def solve(self):
        plaintext = None
        ciphertext = None
        
        try:
            size_mb = self.read_input()
            plaintext = self.generate_data(size_mb)
            key = self.generate_key(16)
            
            plaintext_size = len(plaintext)
            
            ciphertext = self.parallel_encrypt_xor(plaintext, key)
            
            del plaintext
            plaintext = None
            gc.collect()
            
            self.write_output(key, ciphertext, plaintext_size)
            
            del ciphertext
            ciphertext = None
            gc.collect()
            
        except Exception as e:
            if plaintext is not None:
                del plaintext
            if ciphertext is not None:
                del ciphertext
            gc.collect()
            
            f = open(self.output_file_name, 'w')
            f.write("ERROR: %s\n" % str(e))
            f.close()
            raise
    
    def generate_key(self, length=16):
        characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        key = ''.join([random.choice(characters) for _ in range(length)])
        return key
    
    def generate_data(self, size_mb):
        size_bytes = size_mb * 1024 * 1024
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,!?\n'
        
        data = bytearray()
        chunk_size = 1024 * 1024
        remaining = size_bytes
        
        while remaining > 0:
            current_chunk = min(chunk_size, remaining)
            chunk = ''.join([random.choice(chars) for _ in range(current_chunk)])
            data.extend(chunk.encode('utf-8'))
            remaining -= current_chunk
        
        return bytes(data)
    
    def parallel_encrypt_xor(self, data, key):
        if not isinstance(data, bytes):
            data = str(data).encode('utf-8')
        
        data_size = len(data)
        num_workers = len(self.workers)
        chunk_size = data_size // num_workers
        
        tasks = []
        for i in range(num_workers):
            start = i * chunk_size
            end = start + chunk_size if i < num_workers - 1 else data_size
            
            task = {
                'data': data[start:end],
                'key': key,
                'offset': start
            }
            tasks.append(task)
        
        results = []
        futures = []
        for i in range(num_workers):
            future = self.workers[i].encrypt_data(tasks[i])
            futures.append(future)

        for future in futures:
            results.append(future.value)

        encrypted = b''.join(results)
        
        del tasks
        gc.collect()
        
        return encrypted
    
    @staticmethod
    @expose
    def encrypt_data(task):
        data = task['data']
        key = task['key']
        offset = task['offset']
        
        try:
            if not isinstance(key, bytes):
                key_bytes = bytearray(str(key).encode('utf-8'))
            else:
                key_bytes = bytearray(key)
            
            key_len = len(key_bytes)
            encrypted = bytearray()
            
            for i in range(len(data)):
                key_index = (offset + i) % key_len
                
                if isinstance(data[i], int):
                    data_byte = data[i]
                else:
                    data_byte = ord(data[i])
                
                encrypted_byte = data_byte ^ key_bytes[key_index]
                encrypted.append(encrypted_byte)
            
            result = bytes(encrypted)
            
            del data
            del encrypted
            gc.collect()
            
            return result
            
        except Exception:
            gc.collect()
            raise
    
    def read_input(self):
        f = open(self.input_file_name, 'r')
        try:
            size_mb = int(f.read().strip())
        finally:
            f.close()
        return size_mb
    
    def write_output(self, key, ciphertext, plaintext_size):
        f = None
        try:
            f = open(self.output_file_name, 'w')
            
            f.write("Generated Encryption Key:\n")
            f.write("%s\n\n" % key)
            
            f.write("Original data size: %d bytes (%.2f MB)\n" % 
                    (plaintext_size, plaintext_size / (1024.0 * 1024.0)))
            f.write("Encrypted data size: %d bytes (%.2f MB)\n\n" % 
                    (len(ciphertext), len(ciphertext) / (1024.0 * 1024.0)))
            
            f.write("Encrypted data:\n")
            
            sample_size = min(1000, len(ciphertext))
            
            for i in range(sample_size):
                byte_val = ciphertext[i]
                if not isinstance(byte_val, int):
                    byte_val = ord(byte_val)
                
                f.write('%02x' % byte_val)
                
                if (i + 1) % 32 == 0:
                    f.write('\n')
            
            
        finally:
            if f is not None:
                f.close()