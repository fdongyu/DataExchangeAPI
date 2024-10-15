# Exchange Server Setup

## (Jetstream) Step 0. Making an Instance:

You will need the allocation in exosphere in order to do this step, so follow the getting started page.
1. Click the "Create" button on the right hand side.
2. Click "Instance"
3. I recommend either Ubuntu instances. 
4. Name your instance. __This will be part of the server's URL__.
5. For flavor, you only need a g3.small. 
    - Web desktop is up to you. It will make a remote desktop link available to you if you would like.
6. Then hit "create" and exosphere will spin up a new instance for you.

Now you can look at your instances. You should be sent back to the screen you saw the "Create" button. There will be a new item in the instances box with an orange icon that says "building" next your instance name. 

7. Click on "Instances" then your instance.
8. From here, you can enter web shell, desktop, or console when it finishes building. 

> **_NOTE:_**  For the sake of not wasting credits, you should shelve the instance when you're not using it. This can be done with the "Actions" dropdown on the right-hand side under "Create". 

Lastly, there is documentation for [Jetstream](https://docs.jetstream-cloud.org/) in case you need it. 

-------------------------------------------------------------------------------------------------
## Step 1.) Caddy: - not necessary if you deploy with docker
You'll need to install [Caddy](https://caddyserver.com/docs/install), which is an automated HTTP/s server application. 

1. Install [caddy](https://caddyserver.com/docs/install). Instructions are from website. If they don't work, follow the caddy link.
```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

2. In the project directory, make a file named Caddyfile (with uppercase C). Inside, you'll write:
```bash
# Change this to your domain name. <instance_name>.cis240199.projects.jetstream-cloud.org
<instance_name>.<allocation>.projects.jetstream-cloud.org

# Change this to the IP address the server is running.
# If this is in a docker container and you're not using the 
# host network, switch this to the name of the container.
#
# if you have `container_name: server` you will write
# `reverse_proxy server:port`
#
reverse_proxy 0.0.0.0:8000

# Can comment this out. It will display verbose logs to console.
#log {
#output stdout
#}
```

3. While in the project directory, run caddy start so caddy will run in the background. 
- If it gives you an error, it might say some program is already running on port 443 (HTTPS) or 80 (HTTP), you can do `sudo caddy start` or `sudo systemctl start caddy` and it should work. Otherwise investigate what is using those ports.

> **_NOTE:_**
You may need to stop caddy when you reenter the instance if it starts at startup. `caddy stop` or `sudo systemctl start caddy`. To disable the automatic startup, run `sudo systemctl disable caddy`. This won't disable it entirely, it only stops it from running at startup.

### Step 2.) Old Server version:

**Install caddy if you wish to connect with devices outside your instance**

1. First install pip if its not already installed.  
``sudo apt-get install pip3``  
2. Then you can install the requirements.  
`pip install fastapi==0.110.1 uvicorn==0.29.0 pydantic==2.7.0`  
3. Finally you should be able to run the server:  
```python3 -m uvicorn src.server.exchange_server:app ```

If you get an import path error (from something within the project), run:   
```export PYTHONPATH=~/Data-Exchange-Service-for-Computational-Model-Integrations-between-different-platforms/src:$PYTHONPATH``` 

You can change the server (local) IP and port with --host and --port, but it should run on 0.0.0.0 and 8000 by default. **The IP address and port should match the caddy file on the reverse_proxy line**. You may also change the IP in the caddy file to match the server. If the --host and --port args don't change anything, edit the bottom of exchange_server.py. 

> **_NOTE:_**
If you exit your connection to the instance, **the server will stop running if you don't run it with nohup**. So if you want to keep the server running, add nohup before your commands to start the server. E.g. `nohup python3 -m uvicorn src.server.exchange_server:app &` (notice the & at the end).


## Step 3.) New Server verison:

When you start transitioning to my code, you can run the server using similar instructions as above. If you don't use docker, the you need to install caddy using the instructions above.

### With docker (preinstalled on Jetstream):
1. Clone this repo  
```bash
git clone https://github.com/Seth-Wolfgang/Data-Exchange-API.git
cd Data-Exchange-API
```
2. Edit `Caddyfile`. Change the top line to your domain name or public IP.
```bash
# Change this to your domain name. Format on Jetstream: <instance_name>.<allocation>.projects.jetstream-cloud.org
<instance_name>.<allocation>.projects.jetstream-cloud.org
```
3. You can edit the log settings at the bottom if you wish.  
4. Lastly, run docker compose
```bash
docker compose up
```

### Without docker:
1. Clone repo
```bash
git clone https://github.com/Seth-Wolfgang/Data-Exchange-API.git
cd Data-Exchange-API
```
2. Install [caddy](https://caddyserver.com/docs/install). (see above)   
3. Edit `Caddyfile`. Change the top line to your domain name or public IP.  
```bash
# Change this to your domain name. Format on Jetstream: <instance_name>.<allocation>.projects.jetstream-cloud.org
<instance_name>.<allocation>.projects.jetstream-cloud.org
```
4. Finally, install the package and run the server with uvicorn.
```bash
Run pip install . 
python3 -m uvicorn src.server.exchange_server:app
```
> **_NOTE:_**
If you exit your connection to the instance, **the server will stop running if you don't run it with nohup**. So if you want to keep the server running, add nohup before your commands to start the server. E.g. `nohup python3 -m uvicorn src.server.exchange_server:app &` (notice the & at the end).