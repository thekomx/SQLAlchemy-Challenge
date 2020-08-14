import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

engine = create_engine('sqlite:///Resources/hawaii.sqlite')
Base = automap_base()
Base.prepare(engine, reflect=True)

app = Flask(__name__)

@app.route('/')
def index():
    rtn_text = 'Avairable Routes :<br>'
    rtn_text +=' - /api/v1.0/precipitation<br>'
    rtn_text +=' - /api/v1.0/stations<br>'
    rtn_text +=' - /api/v1.0/tobs<br>'
    rtn_text +=' - /api/v1.0/<br>'

    return rtn_text


@app.route('/api/v1.0/precipitation')
def prcp():
    Prcp = Base.classes.measurement
    session = Session(engine)

    date_prcp_dict = []
    date_prcp = session.query(Prcp.date, Prcp.prcp).all()
    for dp in date_prcp:
        date_prcp_dict.append({dp.date : dp.prcp})

    return jsonify(date_prcp_dict)


@app.route('/api/v1.0/stations')
def stations():
    Station = Base.classes.station
    session = Session(engine)

    station_dict = []
    station = session.query(Station).all()
    for stn in station:
        station_dict.append({'ID' : stn.id, 'Station' : stn.station, 'Name' : stn.name, 'Latitude' : stn.latitude, 'Longitude' : stn.longitude, 'Elevation' : stn.elevation})

    return jsonify(station_dict)


@app.route('/api/v1.0/tobs')
def tobs():
    Measurement = Base.classes.measurement
    Station = Base.classes.station
    session = Session(engine)

    the_station = session.query(Measurement.station, Station.name, func.max(Measurement.date).label('date'), func.count(Measurement.station)).group_by(Measurement.station).filter(Station.station == Measurement.station).order_by(func.count(Measurement.station).desc())[0]
    last_date = dt.datetime.strptime(the_station.date, '%Y-%m-%d').date()
    max_date = dt.datetime(last_date.year-1, last_date.month, last_date.day)
    min_date = dt.datetime(last_date.year-2, last_date.month, last_date.day)

    station_tobs = session.query(Measurement.date, Measurement.tobs).filter(Measurement.station == the_station.station).filter(func.date(Measurement.date) <= max_date, func.date(Measurement.date) > min_date).all()

    station_tobs_dict = []
    for stbs in station_tobs:
        station_tobs_dict.append({stbs.date : stbs.tobs})

    return jsonify({the_station.name : station_tobs_dict})


@app.route('/api/v1.0/<start>')
@app.route('/api/v1.0/<start>/<end>')
def date_range(start, end=''):
    start = start.strip()
    end = end.strip()
    err_msg = ''

    try:
        start = dt.datetime.strptime(start, '%Y-%m-%d')
        if end != '':
            end = dt.datetime.strptime(end, '%Y-%m-%d')
            if start > end:
                start, end = end, start
    except ValueError:
        err_msg = 'Incorrect date format!<br>"YYYY-MM-DD" format only.<br>Please try again.'

    if err_msg != '':
        return_value = err_msg
    else:
        Measurement = Base.classes.measurement
        session = Session(engine)

        tobs_describe = session.query(func.min(Measurement.tobs).label('min'), func.max(Measurement.tobs).label('max'), func.avg(Measurement.tobs).label('avg')).filter(func.date(Measurement.date) >= start)
        if end != '':
            tobs_describe = tobs_describe.filter(func.date(Measurement.date) <= end)

        tobs_describe_dict = []
        for td in tobs_describe:
            tobs_describe_dict.append({'TMIN' : td.min, 'TMAX' : td.max, 'TAVG' : td.avg})

        return_value = jsonify(tobs_describe_dict)

    return return_value


if __name__ == "__main__":
    app.run(debug=True)