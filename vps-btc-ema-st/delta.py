"""Delta India REST client. No order retries; ambiguous results fail closed."""
import hashlib,hmac,json,time
from urllib.parse import urlencode
import requests

class DeltaError(RuntimeError):pass

class Delta:
    def __init__(self,config):
        self.conf=config
        self.session=requests.Session()
        self.session.headers.update({"Accept":"application/json","User-Agent":"btc-ema-st-vps/1.0"})
    def request(self,method,path,params=None,body=None,auth=False,envelope=False):
        query=("?"+urlencode(list(params.items()))) if params else ""
        payload=json.dumps(body,ensure_ascii=False,separators=(",",":")) if body is not None else ""
        hdr={}
        if body is not None:hdr["Content-Type"]="application/json"
        if auth:
            if not (self.conf.key and self.conf.secret):
                raise DeltaError("API credentials not configured")
            stamp=str(int(time.time()))
            signed=(method+stamp+path+query+payload).encode()
            sig=hmac.new(self.conf.secret.encode(),signed,hashlib.sha256).hexdigest()
            hdr.update({"api-key":self.conf.key,"timestamp":stamp,"signature":sig})
        # Do not auto-retry a POST/PUT/DELETE: outcome may be unknown after timeout.
        try:
            r=self.session.request(method,self.conf.base_url+path+query,
                 data=payload or None,headers=hdr,timeout=(3,12))
            if r.status_code>=400:
                raise DeltaError("HTTP "+str(r.status_code)+" "+r.text[:320])
            data=r.json()
            if not isinstance(data,dict):
                raise DeltaError("Malformed Delta API response (expected object)")
            if data.get("success") is not True:
                raise DeltaError("API rejected request: "+str(data.get("error",data))[:320])
            return data if envelope else data.get("result",data)
        except requests.RequestException as e:
            raise DeltaError("Transport outcome unclear: "+str(e)) from e
    def product(self,symbol="BTCUSD"):
        return self.request("GET","/v2/products/"+symbol)
    def ticker(self,symbol="BTCUSD"):
        return self.request("GET","/v2/tickers/"+symbol)
    def candles(self,start,end,symbol="BTCUSD",resolution="15m"):
        return self.request("GET","/v2/history/candles",
                            {"resolution":resolution,"symbol":symbol,"start":int(start),"end":int(end)})
    def position(self,product_id):
        return self.request("GET","/v2/positions",{"product_id":int(product_id)},auth=True)
    def wallet(self):
        return self.request("GET","/v2/wallet/balances",auth=True)
    def open_orders(self,product_id):
        return self.request("GET","/v2/orders",
                            {"product_ids":int(product_id),"states":"open,pending"},auth=True)
    def order_by_client_id(self,client_id):
        return self.request("GET","/v2/orders/client_order_id/"+client_id,auth=True)
    def get_leverage(self,product_id):
        return self.request("GET",f"/v2/products/{product_id}/orders/leverage",auth=True)
    def set_leverage(self,product_id,leverage):
        return self.request("POST",f"/v2/products/{product_id}/orders/leverage",
                            body={"leverage":int(leverage)},auth=True)
    def place_order(self,payload):
        return self.request("POST","/v2/orders",body=payload,auth=True)
    def edit_stop(self,product_id,order_id,price):
        return self.request("PUT","/v2/orders",
                            body={"id":int(order_id),"product_id":int(product_id),
                                  "stop_price":str(price)},auth=True)
    def cancel_order(self,product_id,order_id):
        return self.request("DELETE","/v2/orders",
                            body={"id":int(order_id),"product_id":int(product_id)},auth=True)
    def fills(self,product_id,start_microsecond):
        return self.request("GET","/v2/fills",params={"product_ids":int(product_id),
                              "start_time":int(start_microsecond),"page_size":50},auth=True)

    def fills_page(self,product_id,start_us,cursor=None):
        params={"product_ids":int(product_id),"start_time":int(start_us),"page_size":50}
        if cursor:params["after"]=cursor
        return self.request("GET","/v2/fills",params=params,auth=True,envelope=True)
