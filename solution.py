from Pyro4 import expose
import random

try:
    from math import gcd
except ImportError:
    try:
        from fractions import gcd
    except ImportError:
        def gcd(a, b):
            while b:
                a, b = b, a % b
            return a


class Solver:
    def __init__(self, workers=None, input_file_name=None, output_file_name=None):
        self.input_file_name = input_file_name
        self.output_file_name = output_file_name
        self.workers = workers
        self.max_retries = 3
    
    def solve(self):
        
        n = self.read_input()
        
        if n < 2:
            self.write_output([])
            return
        
        if n == 2:
            self.write_output([2])
            return
        
        if n % 2 == 0:
            factors = [2]
            factors.extend(self.factorize_with_workers(n // 2))
            self.write_output(sorted(list(set(factors))))
            return
        
        if self.is_probably_prime(n):
            self.write_output([n])
            return
        
        factors = self.factorize_with_workers(n)
        
        if not factors:
            self.write_output([])
            return
        
        result = sorted(list(set(factors)))
        self.write_output(result)
    
    def factorize_with_workers(self, n):
        for attempt in range(1, self.max_retries + 1):
            
            factors = self.parallel_factorize(n, attempt)
            
            if factors:
                return factors
        
        return []
    
    def parallel_factorize(self, n, attempt_number):
        tasks = []
        num_workers = len(self.workers)
        
        base_iterations = 50000
        max_iterations = base_iterations * attempt_number
        
        random.seed(attempt_number * 1000 + int(n % 1000000))
        
        for i in range(num_workers):
            x0 = random.randint(2, n - 1)
            c = random.randint(1, n - 1)
            tasks.append((n, x0, c, max_iterations))
        
        mapped = []
        for i, worker in enumerate(self.workers):
            mapped.append(worker.factorize_worker(tasks[i]))
        
        for i, result in enumerate(mapped):
            factors = result.value
            
            if factors and len(factors) > 0:
                return factors
        
        return []
    
    @staticmethod
    @expose
    def factorize_worker(params):
        n, x0, c, max_iterations = params
        
        factor = Solver.pollard_rho_internal(n, x0, c, max_iterations)
        
        if not factor or factor == 1 or factor == n:
            return []
        
        factors = []
        factors.extend(Solver.factorize_complete(factor))
        factors.extend(Solver.factorize_complete(n // factor))
        
        return factors
    
    @staticmethod
    def pollard_rho_internal(n, x0, c, max_iterations):
        x = x0
        y = x0
        d = 1
        
        iterations = 0
        while d == 1 and iterations < max_iterations:
            x = (x * x + c) % n
            y = (y * y + c) % n
            y = (y * y + c) % n
            
            d = gcd(abs(x - y), n)
            iterations += 1
        
        if 1 < d < n:
            return d
        else:
            return None
    
    @staticmethod
    def factorize_complete(n):
        if n <= 1:
            return []
        
        if Solver.is_probably_prime(n):
            return [n]
        
        small_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
        for prime in small_primes:
            if n % prime == 0:
                factors = [prime]
                factors.extend(Solver.factorize_complete(n // prime))
                return factors
        
        x0 = random.randint(2, n - 1)
        c = random.randint(1, n - 1)
        factor = Solver.pollard_rho_internal(n, x0, c, 50000)
        
        if factor and factor != 1 and factor != n:
            factors = Solver.factorize_complete(factor)
            factors.extend(Solver.factorize_complete(n // factor))
            return factors
        
        return [n]
    
    @staticmethod
    @expose
    def is_probably_prime(n, k=5):
        if n < 2:
            return False
        if n == 2 or n == 3:
            return True
        if n % 2 == 0:
            return False
        
        r, d = 0, n - 1
        while d % 2 == 0:
            r += 1
            d = d // 2
        
        for _ in range(k):
            a = random.randint(2, n - 2)
            x = pow(a, d, n)
            
            if x == 1 or x == n - 1:
                continue
            
            for _ in range(r - 1):
                x = pow(x, 2, n)
                if x == n - 1:
                    break
            else:
                return False
        
        return True
    
    def read_input(self):
        f = open(self.input_file_name, 'r')
        content = f.read().strip()
        f.close()
        return int(content)
    
    def write_output(self, factors):
        f = open(self.output_file_name, 'w')
        if factors and len(factors) > 0:
            result = ' x '.join([str(x) for x in factors])
            f.write('Factors: ' + result)
        else:
            f.write('Factors not found')
        f.close()