#!/usr/bin/env python
import redis


class RedisFile(object):

  def __init__(self, redis_key, redis_connection=None, auto_del=False, mode='a'):
        # Force self.buf to be a string or unicode
        self.buf = None
        self.len = 0
        self.buflist = []
        self.pos = 0
        self.closed = False
        self.softspace = 0
        self.auto_del = auto_del
        self.read_only = False
        # You can passin an existing redis connection for
        # connection pooling.
        if redis_connection:
            self.redis = redis_connection
        else:
            self.redis = redis.StrictRedis()
        self.redis_key = redis_key

        if mode == 'w' and self.redis.exists(self.redis_key):
          self.redis.delete(self.redis_key)
        elif mode == 'r':
          self.read_only = True

  def _complain_ifclosed(self):
        if self.closed:
            raise ValueError, "I/O operation on closed file"

  def __check_perm(self):
    if self.read_only:
      raise IOError('File not open for writing')

  def isatty(self):
        self._complain_ifclosed()
        return False

  def flush(self):
        self._complain_ifclosed()
        pass

  def write(self, s):
        self._complain_ifclosed()
        self.__check_perm()
        self.redis.rpush(self.redis_key, s)

  def writelines(self, s):
        self._complain_ifclosed()
        self.__check_perm()
        if isinstance(s, str):
            s = s.split('\n')
        self.redis.rpush(self.redis_key, *s)

  def next(self):
        self._complain_ifclosed()
        r = self.readline()
        if not r:
            raise StopIteration
        return r

  def read(self):
        self._complain_ifclosed()
        return "\n".join(self.readlines())

  def readline(self):
        self._complain_ifclosed()
        try:
            data = self.redis.lrange(self.redis_key, self.pos, self.pos)[0]
        except IndexError:
            return None
        self.pos += 1
        return data

  def readlines(self):
        self._complain_ifclosed()
        data = self.redis.lrange(self.redis_key, self.pos, -1)
        self.pos += len(data)
        return data

  # This one should be the offest of the characters not the array index
  def seek(self, s):
        self._complain_ifclosed()
        self.pos = s

  def close(self):
    if self.auto_del:
      self.redis.delete(self.redis_key)
    self.closed = True

  def __str__(self):
        return "%s" % self.__dict__


if __name__ == '__main__':
    f = RedisFile("file")
    f.write('hello')
    f.writelines('hello')
    f.writelines('helloA\nhelloB')
    print f.read()
    print f.read()
    f.seek(0)
    print f.readline()
    print f.read()
    f.close()
