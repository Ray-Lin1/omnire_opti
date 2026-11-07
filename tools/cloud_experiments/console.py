"""Password-authenticated SSH console; password stays only in process memory.

Run interactively, then send one JSON object per line with op=run/upload/download.
Only the task's pinned known-hosts file is accepted. No SSH keys are installed.
"""
import getpass
import json
from pathlib import Path
import sys
import paramiko

client=paramiko.SSHClient()
client.load_host_keys(str(Path('.codex-review/cloud_known_hosts')))
client.set_missing_host_key_policy(paramiko.RejectPolicy())
password=getpass.getpass('Cloud password: ')
client.connect('223.109.239.30',port=31224,username='root',password=password,look_for_keys=False,allow_agent=False,timeout=30)
del password
client.get_transport().set_keepalive(30)
print('CONNECTED',flush=True)
for line in sys.stdin:
    try:
        task=json.loads(line)
        if task['op']=='run':
            _,stdout,stderr=client.exec_command(task['command'],timeout=task.get('timeout',120))
            out=stdout.read().decode(errors='replace'); err=stderr.read().decode(errors='replace')
            print(json.dumps(dict(exit=stdout.channel.recv_exit_status(),stdout=out[-task.get('limit',6000):],stderr=err[-2000:]),ensure_ascii=False),flush=True)
        elif task['op'] in ['upload','download']:
            with client.open_sftp() as sftp:
                if task['op']=='upload':
                    sftp.put(task['local'],task['remote'])
                else:
                    Path(task['local']).parent.mkdir(parents=True,exist_ok=True)
                    sftp.get(task['remote'],task['local'])
            print(json.dumps(dict(op=task['op'],status='done',local=task['local'])),flush=True)
        elif task['op']=='exit':
            break
    except Exception as e:
        print(json.dumps(dict(error=str(e))),flush=True)
client.close()
