import zlib
class BadBook(Exception):pass
class DeltaBook:
    """Exchange sequence+CRC32 verified L2, no snapshot extrapolation."""
    def __init__(self):
        self.asks={};self.bids={};self.seq=None
    @staticmethod
    def apply(book, changes):
        if not isinstance(changes,list):raise BadBook('invalid level array')
        for row in changes:
            if not isinstance(row,list) or len(row)!=2:raise BadBook('invalid level')
            p,s=str(row[0]),str(row[1])
            try:
                if float(p)<=0 or float(s)<0:raise ValueError()
            except ValueError:raise BadBook('invalid price or size')
            if float(s)==0:book.pop(p,None)
            else:book[p]=s
    def checksum(self):
        asks=sorted(self.asks.items(),key=lambda x:float(x[0]))[:10]
        bids=sorted(self.bids.items(),key=lambda x:-float(x[0]))[:10]
        fmt=lambda xs:','.join(f'{p}:{s}' for p,s in xs)
        return zlib.crc32((fmt(asks)+'|'+fmt(bids)).encode('utf8')) & 0xffffffff
    def update(self,m):
        if m.get('type')!='ob_updates' or m.get('sy')!='BTCUSD':raise BadBook('invalid symbol/channel')
        action=m.get('action')
        if action not in ('snapshot','update'):raise BadBook('invalid book action '+str(action))
        try:seq=int(m['seq']);expected=int(m['cs'])
        except (TypeError,ValueError,KeyError):raise BadBook('missing sequence/checksum')
        if action=='snapshot':self.asks={};self.bids={};self.seq=None
        elif self.seq is None or seq!=self.seq+1:
            raise BadBook(f'sequence gap previous={self.seq} current={seq}')
        self.apply(self.asks,m.get('a'));self.apply(self.bids,m.get('b'))
        if not self.asks or not self.bids:raise BadBook('empty book')
        if max(map(float,self.bids))>=min(map(float,self.asks)):raise BadBook('crossed book')
        actual=self.checksum()
        if actual!=expected:raise BadBook(f'checksum mismatch got={actual} expected={expected}')
        self.seq=seq
        return seq
    def checkpoint(self):
        return {'sequence':self.seq,'crc32':self.checksum(),
                'asks':sorted(self.asks.items(),key=lambda x:float(x[0])),
                'bids':sorted(self.bids.items(),key=lambda x:-float(x[0]))}

