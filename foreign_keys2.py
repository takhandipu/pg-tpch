#/usr/bin/python

import time
from datetime import datetime
from multiprocessing import Process, Queue

import psycopg2

# pool size
nprocesses = 8
db_port = '20002'
db_hosts = [
				"xlcloud2", "xlcloud3", "xlcloud4", "xlcloud5", "xlcloud6", "xlcloud7", "xlcloud8", "xlcloud9"
		]

db_connect_str = "dbname=tpch "


commands = [
"ALTER TABLE customer ADD CONSTRAINT customer_c_nationkey_fkey FOREIGN KEY (c_nationkey) REFERENCES nation(n_nationkey)",
"ALTER TABLE lineitem ADD CONSTRAINT lineitem_l_orderkey_fkey FOREIGN KEY (l_orderkey) REFERENCES orders(o_orderkey)",
"ALTER TABLE partsupp ADD CONSTRAINT partsupp_ps_suppkey_fkey FOREIGN KEY (ps_suppkey) REFERENCES supplier(s_suppkey)"
]


def run_commands(i, queue_in, queue_out):

		try:

				conn = psycopg2.connect(db_connect_str + 'host = ' + db_hosts[i] + ' port = ' + db_port)
				cur  = conn.cursor()

				# iterate over results from the queue
				while True:

						# by default we have nothing
						sql = None

						try:
								sql = queue_in.get_nowait()
						except:
							pass

						if sql is None:
							break

						# build the SQL query
						queue_out.put({'type' : 'START', 'time' : datetime.now().strftime('%y-%m-%d %H:%M:%S'), 'sql' : sql})

						start_time = time.time()

						cur.execute(sql)
						conn.commit()

						end_time = time.time()

						# put the output message
						queue_out.put({'type' : 'END', 'time' : datetime.now().strftime('%y-%m-%d %H:%M:%S'), 'sql' : sql, 'duration' : int(end_time - start_time)})

				# close the cursor/connection
				cur.close()
				conn.close()

		except Exception as ex:

				print "process %(id)s failed: %(msg)s" % {'id' : str(i), 'msg' : str(ex)}


def receive_messages(q):
		'receive messages'

		while True:

				m = q.get(True)

				# we only know EXIT and START/END messages

				if m['type'] == 'EXIT':
						break

				elif m['type'] == 'START':
						print "%(time)s %(type)s %(sql)s" % m

				elif m['type'] == 'END':
						print "%(time)s %(type)s %(sql)s %(duration)s" % m


if __name__ == '__main__':

		# input queue (with all the files to print)
		queue_in = Queue()

		# fill the queue (all the commands at once)
		[queue_in.put(c) for c in commands]

		# output messages (not to print garbage)
		queue_out = Queue()

		# create pool of the expected size
		workers = [Process(target=run_commands, args=(i,queue_in,queue_out)) for i in range(nprocesses)]

		# create the process printing messages
		printer = Process(target=receive_messages, args=(queue_out,))

		# start all the workers and printer thread
		[p.start() for p in workers]
		printer.start()

		# wait for all the workers to complete
		[p.join() for p in workers]

		# terminate the message receiver (send message, wait for termination)
		queue_out.put({'type' : 'EXIT'})
		printer.join()

