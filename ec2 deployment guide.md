Below is the most practical AWS deployment path for your current codebase: a single EC2 instance running your Docker Compose stack.

This is the right fit for what you have now because your app is already built around:
- `api`
- `worker`
- `redis`
- `postgres`
- `neo4j`

If later you want, we can evolve this into:
- EC2 + Nginx + SSL
- or ECS/Fargate
- or EC2 + S3 + RDS + managed Redis

But for now, this is the cleanest path.

**Recommended AWS Target**
Use this deployment shape first:

```text
Internet
  -> EC2 public IP / Elastic IP
  -> FastAPI container (port 8000)
  -> Worker container
  -> Redis container
  -> Postgres container
  -> Neo4j container

Persistent on EC2:
- repo code
- backend/data
- docker volumes
```

For production safety, do not expose Redis, Postgres, or Neo4j publicly unless you truly need to.

**Step 1: Create the EC2 Instance**
In AWS Console:
1. Open EC2.
2. Launch instance.
3. Choose `Amazon Linux 2023`.
4. Choose an instance type.
   Good starting point:
   - `t3.large` for light testing
   - `t3.xlarge` or better for real video workloads
5. Create/select a key pair.
6. Storage:
   - use at least `30-50 GB`
   - use more if you will store many videos/snapshots
7. Create or choose a security group.

Recommended inbound rules:
- `22` from your IP only
- `8000` from your IP or from the public internet if you want direct app access
- optionally `80` and `443` later if you add Nginx
- do **not** open:
  - `5432`
  - `6379`
  - `7687`
  - `7474`
  to the world unless you specifically need them

AWS security groups are the official network firewall mechanism for EC2 instances. AWS documents them here:
[EC2 security groups](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html)

**Step 2: Attach an IAM Role**
If you want S3 support from the app:
1. Create an IAM role for EC2.
2. Attach S3 permissions.
   Minimal approach:
   - read/write access only to your target bucket
3. Attach the role to the instance.

AWS recommends IAM roles instead of hardcoding credentials on EC2:
[Attach an IAM role to an instance](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/attach-iam-role.html)
[Using IAM roles on EC2](https://docs.aws.amazon.com/sdkref/latest/guide/access-iam-roles-for-ec2.html)

If you stay with local storage only, this is optional.

**Step 3: Allocate an Elastic IP**
If you want a stable public IP:
1. Allocate Elastic IP
2. Associate it to the EC2 instance

AWS docs:
[Associate an Elastic IP address](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/working-with-eips.html)

This is strongly recommended if you’ll revisit the same deployed app.

**Step 4: SSH Into the Instance**
From your machine:

```powershell
ssh -i path\to\your-key.pem ec2-user@YOUR_EC2_PUBLIC_IP
```

**Step 5: Install Docker on Amazon Linux 2023**
AWS official guidance for AL2023 is effectively:

```bash
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user
```

Then log out and log back in.

Verify:
```bash
docker info
```

AWS reference:
[Install Docker on Amazon Linux 2023](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-docker.html)
Also reflected in ECS docs:
[Create a container image on Amazon ECS docs](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/create-container-image.html)

**Step 6: Install Git**
If not already present:

```bash
sudo yum install -y git
```

**Step 7: Clone Your Repo**
Use your GitHub repo:

```bash
git clone https://github.com/sharanbharadwaj1/urban-traffic-intel.git
cd urban-traffic-intel
git checkout surveillance-tracker-ec2-backend
cd backend
```

You told me that branch now contains the latest backend/dashboard work.

**Step 8: Create the Runtime `.env`**
Inside `backend/`, create `.env`.

You can start from `.env.example`:

```bash
cp .env.example .env
```

Then edit it:

```bash
nano .env
```

Recommended starting values for EC2 local-storage deployment:

```env
APP_NAME=Traffic Video Analytics Service
LOG_LEVEL=INFO

DATABASE_URL=postgresql+psycopg://traffic1:traffic1@postgres:5432/trafficdb1
BROKER_URL=redis://redis:6379/0
RESULT_BACKEND_URL=redis://redis:6379/1

STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=./data/storage
UPLOAD_TEMP_PATH=./data/uploads

MODEL_PATH=yolov8n.pt
CONFIDENCE_THRESHOLD=0.35
FRAME_SKIP=5
FRAME_RESIZE_WIDTH=960
TRACKER_MAX_DISTANCE=80
SAVE_EVENT_SNAPSHOTS=true

PLATE_ENABLED=true
ANPR_API_TOKEN=YOUR_REAL_TOKEN
ANPR_API_URL=https://api.platerecognizer.com/v1/plate-reader/
ANPR_COUNTRY=in
ANPR_MIN_SCORE=0.5

GRAPH_ENABLED=true
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

If you want S3-backed storage instead of local EC2 disk:

```env
STORAGE_BACKEND=s3
STORAGE_BUCKET=your-bucket-name
STORAGE_REGION=ap-south-1
STORAGE_ENDPOINT_URL=
```

If the instance has an IAM role with S3 access, you usually do not need to hardcode AWS keys.

**Step 9: Decide Where the Model Comes From**
Your app uses `MODEL_PATH=yolov8n.pt`.

You have two choices.

Option A: let Ultralytics download it at first run
- easiest
- requires internet access from EC2/container

Option B: place the model file manually in `backend/`
- more predictable
- good for stable deployments

If you want manual placement:

```bash
ls
```

You should see `Dockerfile`, `docker-compose.yml`, `.env`, etc.

Then put `yolov8n.pt` there so the container can access it if your compose/build path expects it.

**Step 10: Start the Stack**
From `backend/`:

```bash
docker compose up --build -d
```

Then verify:

```bash
docker compose ps
```

You want these up:
- `api`
- `worker`
- `redis`
- `postgres`
- `neo4j`

Check logs:

```bash
docker compose logs api --tail=100
docker compose logs worker --tail=100
```

**Step 11: Test the Deployment**
From your browser:

```text
http://YOUR_EC2_PUBLIC_IP:8000/
```

Also test:
- `http://YOUR_EC2_PUBLIC_IP:8000/health`
- dashboard upload flow
- `http://YOUR_EC2_PUBLIC_IP:8000/jobs`
- Neo4j Browser:
  `http://YOUR_EC2_PUBLIC_IP:7474/`
  only if you intentionally exposed that port

For a public deployment, I recommend **not** exposing Neo4j publicly long term.

**Step 12: Persist Data Properly**
Your current compose setup already writes data under `backend/data` and Docker volumes.

Important persistence areas:
- uploaded videos
- snapshots
- live preview files
- Postgres volume
- Neo4j volume

On EC2, these are persistent as long as:
- you keep the EBS disk
- you do not delete the instance or volumes

For real production:
- store raw videos and snapshots in S3
- keep Postgres/Neo4j data on EBS
- take periodic snapshots/backups

**Step 13: Make It Start After Reboot**
Because your compose services use restart policies, Docker will restart containers if Docker itself is running.

But make sure Docker starts on boot:

```bash
sudo systemctl enable docker
sudo systemctl start docker
```

If you want the compose stack itself to come back automatically after an EC2 reboot, the current `restart: unless-stopped` entries are helpful, provided Docker daemon starts.

**Step 14: Recommended Production Hardening**
Once basic deployment works, do these next.

1. Put Nginx in front
- proxy `80/443` to `8000`
- easier domain/SSL setup
- cleaner public exposure

2. Add HTTPS
- use a domain
- terminate TLS with Nginx + Let’s Encrypt
- or place an ALB in front later

3. Restrict security groups
- allow `22` only from your IP
- expose only `80/443`
- do not expose Postgres/Redis/Neo4j publicly

4. Move storage to S3
- best for EC2 durability
- avoids filling root disk with videos/snapshots

5. Move DB out of container later if needed
- RDS for Postgres
- managed Neo4j alternative if your workload grows

6. Add monitoring
- CloudWatch agent or at least container logs
- disk usage checks
- memory usage checks

7. Add backups
- EBS snapshots
- DB dumps
- S3 lifecycle rules

**Step 15: Useful Commands on EC2**
Check status:
```bash
docker compose ps
```

View logs:
```bash
docker compose logs api --tail=200
docker compose logs worker --tail=200
docker compose logs postgres --tail=100
docker compose logs neo4j --tail=100
```

Restart stack:
```bash
docker compose restart
```

Rebuild after code changes:
```bash
git pull
cd backend
docker compose up --build -d
```

Stop stack:
```bash
docker compose down
```

Stop stack but keep volumes:
```bash
docker compose down
```

Stop stack and remove volumes:
```bash
docker compose down -v
```

Be careful with `-v` because it removes Postgres/Neo4j volumes.

**Suggested AWS Deployment Sequence**
If you want the shortest reliable path:

1. Launch EC2 with Amazon Linux 2023
2. Attach IAM role for S3 if needed
3. Assign Elastic IP
4. Install Docker + Git
5. Clone repo
6. Checkout `surveillance-tracker-ec2-backend`
7. Configure `.env`
8. Run `docker compose up --build -d`
9. Open port `8000`
10. Test upload + worker + dashboard
11. Add Nginx + HTTPS after that

**Recommended Final Public Shape**
For a cleaner public deployment, the next shape should be:

```text
Internet
  -> Nginx (80/443)
  -> FastAPI (8000)
  -> Celery worker
  -> Redis
  -> Postgres
  -> Neo4j

Storage:
- S3 for videos/snapshots
- EBS for DB volumes
```

**Big Practical Warning**
Do not publicly expose all compose ports on EC2 for long-term production.

Safe public exposure:
- `80`
- `443`
- maybe `8000` temporarily while testing

Usually private only:
- `5432`
- `6379`
- `7474`
- `7687`

**Sources**
- Amazon Linux 2023 on EC2:
  [AWS AL2023 on EC2](https://docs.aws.amazon.com/linux/al2023/ug/ec2.html)
- Install Docker on AL2023:
  [AWS SAM Docker install doc](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-docker.html)
  [AWS ECS container image guide](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/create-container-image.html)
- EC2 security groups:
  [AWS EC2 security groups](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html)
- Attach IAM role:
  [Attach IAM role to EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/attach-iam-role.html)
  [Use IAM roles on EC2](https://docs.aws.amazon.com/sdkref/latest/guide/access-iam-roles-for-ec2.html)
- Elastic IP:
  [Associate Elastic IP](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/working-with-eips.html)

If you want, I can turn this into a new markdown file in the repo:
- `docs/AWS_EC2_DEPLOYMENT_GUIDE.md`
with exact commands, `.env` template, and a post-deploy checklist.
