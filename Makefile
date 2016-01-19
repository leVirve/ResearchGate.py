all: celery mongo


celery:
	celery -A rgparse worker -l info --concurrency=10 > ./tmp/log.txt 2>&1 &

mongo:
	@mkdir data tmp
	./mongod > ./tmp/log.txt 2>&1 &

close:
	-mongod --dbpath=data --shutdown
	-ps auxww | grep '[c]elery -A' | awk '{print $$2}' | xargs kill -9

clean:
	-@rm -rf data/ tmp/
