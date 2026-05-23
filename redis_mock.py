#!/usr/bin/env python3
"""Lightweight in-memory Redis mock server for Helix local dev."""
import asyncio
import time

# In-memory Redis state
kv_store = {}
queues = {}
zsets = {}

async def read_command(reader):
    line = await reader.readline()
    if not line:
        return None
    if not line.startswith(b'*'):
        # Handle inline commands like PING
        parts = line.decode('utf-8', errors='ignore').strip().split()
        return parts
    
    try:
        num_args = int(line[1:-2])
    except ValueError:
        return None
        
    args = []
    for _ in range(num_args):
        len_line = await reader.readline()
        if not len_line or not len_line.startswith(b'$'):
            return None
        try:
            arg_len = int(len_line[1:-2])
        except ValueError:
            return None
        
        arg_data = await reader.readexactly(arg_len)
        await reader.readexactly(2)  # Trailing \r\n
        args.append(arg_data.decode('utf-8', errors='ignore'))
    return args

async def handle_client(reader, writer):
    peer = writer.get_extra_info('peername')
    print(f"[*] New connection from {peer}")
    try:
        while True:
            args = await read_command(reader)
            if not args:
                break
                
            cmd = args[0].upper()
            print(f"[>] Command: {cmd} {args[1:]}")
            
            if cmd == "PING":
                writer.write(b"+PONG\r\n")
            elif cmd == "AUTH":
                writer.write(b"+OK\r\n")
            elif cmd == "SELECT":
                writer.write(b"+OK\r\n")
            elif cmd == "CLIENT":
                writer.write(b"+OK\r\n")
            elif cmd == "CONFIG":
                writer.write(b"+OK\r\n")
            elif cmd == "GET":
                key = args[1]
                val = kv_store.get(key)
                if val is None:
                    writer.write(b"$-1\r\n")
                else:
                    writer.write(f"${len(val)}\r\n{val}\r\n".encode('utf-8'))
            elif cmd == "SET":
                key = args[1]
                val = args[2]
                # Check for NX
                nx = "NX" in [a.upper() for a in args[3:]]
                if nx and key in kv_store:
                    writer.write(b"$-1\r\n")
                else:
                    kv_store[key] = val
                    writer.write(b"+OK\r\n")
            elif cmd in ("RPUSH", "LPUSH"):
                key = args[1]
                values = args[2:]
                if key not in queues:
                    queues[key] = asyncio.Queue()
                for val in values:
                    queues[key].put_nowait(val)
                writer.write(f":{queues[key].qsize()}\r\n".encode('utf-8'))
            elif cmd == "BLPOP":
                keys = args[1:-1]
                try:
                    timeout = float(args[-1])
                except ValueError:
                    timeout = 0
                
                popped_val = None
                popped_key = None
                
                # Check immediate
                for key in keys:
                    q = queues.get(key)
                    if q and not q.empty():
                        popped_val = q.get_nowait()
                        popped_key = key
                        break
                
                if popped_val is not None:
                    resp = f"*2\r\n${len(popped_key)}\r\n{popped_key}\r\n${len(popped_val)}\r\n{popped_val}\r\n".encode('utf-8')
                    writer.write(resp)
                else:
                    # Polled wait (suitable for local dev mock)
                    start_time = time.time()
                    while time.time() - start_time < timeout:
                        for key in keys:
                            q = queues.get(key)
                            if q and not q.empty():
                                popped_val = q.get_nowait()
                                popped_key = key
                                break
                        if popped_val is not None:
                            break
                        await asyncio.sleep(0.05)
                        
                    if popped_val is not None:
                        resp = f"*2\r\n${len(popped_key)}\r\n{popped_key}\r\n${len(popped_val)}\r\n{popped_val}\r\n".encode('utf-8')
                        writer.write(resp)
                    else:
                        writer.write(b"*-1\r\n")
            elif cmd == "ZADD":
                key = args[1]
                pairs = args[2:]
                if key not in zsets:
                    zsets[key] = {}
                added = 0
                for i in range(0, len(pairs), 2):
                    score = float(pairs[i])
                    member = pairs[i+1]
                    zsets[key][member] = score
                    added += 1
                writer.write(f":{added}\r\n".encode('utf-8'))
            elif cmd == "ZRANGEBYSCORE":
                key = args[1]
                min_val = float(args[2])
                max_val = float(args[3])
                
                limit_offset = None
                limit_count = None
                for idx, arg in enumerate(args):
                    if arg.upper() == "LIMIT":
                        limit_offset = int(args[idx+1])
                        limit_count = int(args[idx+2])
                        break
                        
                zset = zsets.get(key, {})
                items = []
                for member, score in zset.items():
                    if min_val <= score <= max_val:
                        items.append((member, score))
                items.sort(key=lambda x: x[1])
                
                if limit_offset is not None:
                    items = items[limit_offset:limit_offset+limit_count]
                    
                writer.write(f"*{len(items)}\r\n".encode('utf-8'))
                for member, _ in items:
                    writer.write(f"${len(member)}\r\n{member}\r\n".encode('utf-8'))
            elif cmd == "ZREMRANGEBYSCORE":
                key = args[1]
                min_val = float(args[2])
                max_val = float(args[3])
                
                zset = zsets.get(key, {})
                to_remove = []
                for member, score in zset.items():
                    if min_val <= score <= max_val:
                        to_remove.append(member)
                        
                for member in to_remove:
                    del zset[member]
                    
                writer.write(f":{len(to_remove)}\r\n".encode('utf-8'))
            elif cmd == "PUBLISH":
                writer.write(b":0\r\n")
            else:
                print(f"[!] Unsupported command: {cmd}")
                writer.write(b"-ERR unknown command\r\n")
            
            await writer.drain()
    except Exception as e:
        print(f"[!] Error handling client: {e}")
    finally:
        print(f"[*] Connection from {peer} closed")
        writer.close()
        await writer.wait_closed()

async def main():
    server = await asyncio.start_server(handle_client, '127.0.0.1', 6379)
    addr = server.sockets[0].getsockname()
    print(f"[*] Serving Redis Mock on {addr}")
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[*] Redis Mock Server stopped")
