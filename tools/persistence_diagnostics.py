"""Opt-in diagnostics. These runs are never eligible for performance publication."""
from datetime import datetime, timezone
import json

JFR_FLAG = ('-XX:StartFlightRecording=filename=/tmp/persistence.jfr,settings=profile,dumponexit=true,'
            'maxsize=64m,jdk.ExecutionSample#period=2ms')
PG_FLAGS = ['-c','shared_preload_libraries=pg_stat_statements',
            '-c','pg_stat_statements.track=all','-c','pg_stat_statements.track_planning=on']


class PersistenceDiagnostics:
    def __init__(self, output, variant, run, app, db, database, docker, psql):
        self.output, self.prefix = output, f'{variant}-{run}'
        self.app, self.db, self.database = app, db, database
        self.docker, self.psql = docker, psql
        self.data = dict(instrumented=True, performanceComparison=False, variant=variant,
                         run=run, marks=[], sql={})

    def mark(self, name, sql=False):
        self.data['marks'].append(dict(event=name, at=datetime.now(timezone.utc).isoformat()))
        if sql:
            query = """select coalesce(json_agg(t),'[]') from (
                select queryid::text,toplevel,query,calls,plans,total_plan_time,total_exec_time,rows
                from pg_stat_statements
                where dbid=(select oid from pg_database where datname=current_database())
                  and query not like '%pg_stat_statements%'
                order by total_exec_time desc) t;"""
            self.data['sql'][name] = json.loads(self.psql(self.db,query,self.database).stdout)
        self.save()

    def save(self):
        (self.output/f'{self.prefix}.profile.json').write_text(json.dumps(self.data,indent=2)+'\n',encoding='utf-8')

    def collect(self):
        self.docker('cp',self.app+':/tmp/persistence.jfr',str(self.output/f'{self.prefix}.jfr'))
        if self.data['variant'] == 'guicedee':
            self.docker('cp',self.app+':/tmp/diagnostics/startup.json',str(self.output/f'{self.prefix}.startup.json'))
        self.save()
