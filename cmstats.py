import bs4 as bs
import os
import os.path
import datetime
from urllib.request import urlopen

# rrdtool dump test.rrd > test.xml

cm_status_url = 'http://192.168.100.1/cmconnectionstatus.html'
db_path = '/home/lcladmin/cmstats/'
web_path = '/var/www/html/cmstats/'

def parse_cmstatus(source):
    soup = bs.BeautifulSoup(source, 'lxml')
    tables = soup.find_all('table', attrs={'class':'simpleTable'})

    ds_table = tables[1]

    ds_channels = ds_table.find_all('tr', attrs={'align':'left'})

    ds = []

    for ds_channel in ds_channels:
        cols = ds_channel.find_all('td')

        channel_id = cols[0].text.strip()
        lock_status = cols[1].text.strip()
        modulation = cols[2].text.strip()
        raw_frequency = cols[3].text.strip()
        raw_power = cols[4].text.strip()
        raw_snr = cols[5].text.strip()
        corrected = cols[6].text.strip()
        uncorrected = cols[7].text.strip()

        # print('* downstream channel raw values *')
        # print('channel id: ' + channel_id)
        # print('lock status: ' + lock_status)
        # print('modulation: ' + modulation)
        # print('frequency: ' + raw_frequency)
        # print('power: ' + raw_power)
        # print('snr: ' + raw_snr)
        # print('corrected: ' + corrected)
        # print('uncorrected: ' + uncorrected)

        frequency = raw_frequency.replace(' Hz', '')
        power = raw_power.replace(' dBmV', '')
        snr = raw_snr.replace(' dB', '')

        # print('* downstream channel parsed values *')
        # print('frequency: ' + frequency)
        # print('power: ' + power)
        # print('snr: ' + snr)
        # print('corrected: ' + corrected)
        # print('uncorrected: ' + uncorrected)

        ds_channel_values = {
            'frequency': frequency,
            'power': power,
            'snr': snr,
            'corrected': corrected,
            'uncorrected': uncorrected
        }

        ds.append(ds_channel_values)

    us_table = tables[2]

    us_channels = us_table.find_all('tr', attrs={'align':'left'})

    us = []

    for us_channel in us_channels:
        cols = us_channel.find_all('td')

        channel = cols[0].text.strip()
        channel_id = cols[1].text.strip()
        lock_status = cols[2].text.strip()
        modulation = cols[3].text.strip()
        raw_frequency = cols[4].text.strip()
        raw_width = cols[5].text.strip()
        raw_power = cols[6].text.strip()

        # print('* upstream channel raw values *')
        # print('channel: ' + channel)
        # print('channel id: ' + channel_id)
        # print('lock status: ' + lock_status)
        # print('modulation: ' + modulation)
        # print('frequency: ' + raw_frequency)
        # print('width: ' + raw_width)
        # print('power: ' + raw_power)

        frequency = raw_frequency.replace(' Hz', '')
        width = raw_width.replace(' Hz', '')
        power = raw_power.replace(' dBmV', '')

        # print('* upstream channel parsed values *')
        # print('frequency: ' + frequency)
        # print('width: ' + width)
        # print('power: ' + power)

        us_channel_values = {
            'frequency': frequency,
            'width': width,
            'power': power
        }

        us.append(us_channel_values)

    ret = {
        'downstream': ds,
        'upstream': us
    }

    return ret

def get_frequency_value(elem):
    return int(elem['frequency'])

def update_rrd(channels):
    # sort channels by frequency

    channels['downstream'] = sorted(channels['downstream'], key=get_frequency_value)
    channels['upstream'] = sorted(channels['upstream'], key=get_frequency_value)

    db_ext = '.rrd'
    img_ext = '.png'

    # **** DOWNSTREAM ****

    ds_path = db_path + 'data/downstream/'

    graph_path = web_path

    index_contents = str(
        '<html><head><title>Cable Modem Statistics</title></head><body>' +
        '<h2>Cable Modem Statistics</h2>' +
        '<h3>Last Update</h3>' +
        '<p>' + datetime.datetime.utcnow().isoformat() + '</p>'
    )

    index_page_ds_summary_contents = str(
        '<h3>Downstream Channels Summary</h3>' +
        '<table border="1">' +
        '<tr>' +
        '<th>Frequency (Hz)</th>' +
        '<th>Power (dBm)</th>' +
        '<th>SNR (dB)</th>' +
        '<th>Corrected (Symbols)</th>' +
        '<th>Uncorrected (Symbols)</th>' +
        '</tr>'
    )

    # power

    ds_power_all_path = graph_path + 'downstream_all_power' + img_ext

    ds_power_all_cmd = str(
        'rrdtool graph ' + ds_power_all_path + ' -a PNG ' +
        '--width 800 --height 400 --title "Power" ' +
        '--vertical-label "dBm" --disable-rrdtool-tag '
    )

    # snr

    ds_snr_all_path = graph_path + 'downstream_all_snr' + img_ext

    ds_snr_all_cmd = str(
        'rrdtool graph ' + ds_snr_all_path + ' -a PNG ' +
        '--width 800 --height 400 --title "SNR" ' +
        '--vertical-label "dB" --disable-rrdtool-tag '
    )

    # corrected

    ds_corrected_all_path = graph_path + 'downstream_all_corrected' + img_ext

    ds_corrected_all_cmd = str(
        'rrdtool graph ' + ds_corrected_all_path + ' -a PNG ' +
        '--width 800 --height 400 --title "Corrected" ' +
        '--vertical-label "Symbols" --disable-rrdtool-tag '
    )

    # uncorrected

    ds_uncorrected_all_path = graph_path + 'downstream_all_uncorrected' + img_ext

    ds_uncorrected_all_cmd = str(
        'rrdtool graph ' + ds_uncorrected_all_path + ' -a PNG ' +
        '--width 800 --height 400 --title "Uncorrected" ' +
        '--vertical-label "Symbols" --disable-rrdtool-tag '
    )

    for ds_channel in channels['downstream']:
        frequency = ds_channel['frequency']
        power = ds_channel['power']
        snr = ds_channel['snr']
        corrected = ds_channel['corrected']
        uncorrected = ds_channel['uncorrected']

        ds_ch_path = ds_path + frequency + db_ext

        if (not os.path.exists(ds_ch_path)):
            os.system(
                'rrdtool create ' + ds_ch_path + ' ' +
                '--start N --step 300 ' +
                'DS:power:GAUGE:600:U:U ' +
                'DS:snr:GAUGE:600:U:U ' +
                'DS:corrected:DERIVE:600:0:U ' +
                'DS:uncorrected:DERIVE:600:0:U ' +
                'RRA:AVERAGE:0.5:1:1440'
            )

        os.system(
            'rrdtool update ' + ds_ch_path + ' ' +
            'N:' + power + ':' + snr + ':' + corrected + ':' + uncorrected
        )

        # power

        power_graph_path = graph_path + 'downstream_' + frequency + '_power' + img_ext

        ds_power_ch_cmd = str(
            'rrdtool graph ' + power_graph_path + ' -a PNG --title="' + frequency + ' Hz" ' +
            '--vertical-label "dBm" --disable-rrdtool-tag ' +
            'DEF:power=' + ds_ch_path + ':power:AVERAGE ' +
            'LINE1:power#ff0000:Power'
        )

        os.system(ds_power_ch_cmd)

        ds_power_all_cmd = ds_power_all_cmd + str(
            'DEF:' + frequency + '=' + ds_ch_path + ':power:AVERAGE ' +
            'LINE1:' + frequency + '#ff0000:' + frequency + 'Hz '
        )

        # snr

        snr_graph_path = graph_path + 'downstream_' + frequency + '_snr' + img_ext

        ds_snr_ch_cmd = str(
            'rrdtool graph ' + snr_graph_path + ' -a PNG --title="' + frequency + ' Hz" ' +
            '--vertical-label "dB" --disable-rrdtool-tag ' +
            'DEF:snr=' + ds_ch_path + ':snr:AVERAGE ' +
            'LINE1:snr#ff0000:SNR'
        )

        os.system(ds_snr_ch_cmd)

        ds_snr_all_cmd = ds_snr_all_cmd + str(
            'DEF:' + frequency + '=' + ds_ch_path + ':snr:AVERAGE ' +
            'LINE1:' + frequency + '#ff0000:' + frequency + 'Hz '
        )

        # corrected

        corrected_graph_path = graph_path + 'downstream_' + frequency + '_corrected' + img_ext

        ds_corrected_ch_cmd = str(
            'rrdtool graph ' + corrected_graph_path + ' -a PNG --title="' + frequency + ' Hz" ' +
            '--vertical-label "Symbols" --disable-rrdtool-tag ' +
            'DEF:corrected=' + ds_ch_path + ':corrected:AVERAGE ' +
            'LINE1:corrected#ff0000:Corrected'
        )

        os.system(ds_corrected_ch_cmd)

        ds_corrected_all_cmd = ds_corrected_all_cmd + str(
            'DEF:' + frequency + '=' + ds_ch_path + ':corrected:AVERAGE ' +
            'LINE1:' + frequency + '#ff0000:' + frequency + 'Hz '
        )

        # uncorrected

        uncorrected_graph_path = graph_path + 'downstream_' + frequency + '_uncorrected' + img_ext

        ds_uncorrected_ch_cmd = str(
            'rrdtool graph ' + uncorrected_graph_path + ' -a PNG --title="' + frequency + ' Hz" ' +
            '--vertical-label "Symbols" --disable-rrdtool-tag ' +
            'DEF:uncorrected=' + ds_ch_path + ':uncorrected:AVERAGE ' +
            'LINE1:uncorrected#ff0000:Uncorrected'
        )

        os.system(ds_uncorrected_ch_cmd)

        ds_uncorrected_all_cmd = ds_uncorrected_all_cmd + str(
            'DEF:' + frequency + '=' + ds_ch_path + ':uncorrected:AVERAGE ' +
            'LINE1:' + frequency + '#ff0000:' + frequency + 'Hz '
        )

        # power

        lower_power_limit = -15
        upper_power_limit = 15

        if ((float(power) > lower_power_limit) and (float(power) < upper_power_limit)):
            power_style = ' style="background-color:#00FF00"'
        else:
            power_style = ' style="background-color:#FF0000"'

        # snr

        lower_snr_limit = 0

        if ((float(power) > -15) and (float(power) < -6)):
            lower_snr_limit = 33

            if ((float(snr)) > lower_snr_limit):
                snr_style = ' style="background-color:#00FF00"'
            else:
                snr_style = ' style="background-color:#FF0000"'
        elif ((float(power) > -6) and (float(power) < 15)):
            lower_snr_limit = 30

            if ((float(snr)) > lower_snr_limit):
                snr_style = ' style="background-color:#00FF00"'
            else:
                snr_style = ' style="background-color:#FF0000"'
        else:
            lower_snr_limit = 33

            if ((float(snr)) > lower_snr_limit):
                snr_style = ' style="background-color:#00FF00"'
            else:
                snr_style = ' style="background-color:#FF0000"'

        index_page_ds_summary_contents = index_page_ds_summary_contents + str(
            '<tr>' +
            '<td><a href="downstream_' + frequency + '.html">' + frequency + '</a></td>' +
            '<td' + power_style + '>' + power + '</td>' +
            '<td' + snr_style + '>' + snr + '</td>' +
            '<td>' + corrected + '</td>' +
            '<td>' + uncorrected + '</td>' +
            '</tr>'
        )

        ch_page_contents = str(
            '<html><head><title>Downstream Channel Details (' + frequency + ' Hz)</title></head><body>' +
            '<h2>Downstream Channel Details (' + frequency + ' Hz)</h2>' +
            '<h3>Last Update</h3>' +
            '<p>' + datetime.datetime.utcnow().isoformat() + '</p>' +
            '<h3>Downstream Channel Summary</h3>' +
            '<table border="1">' +
            '<tr>' +
            '<th>Frequency (Hz)</th>' +
            '<th>Lower Power Limit (dBm)</th>' +
            '<th>Actual Power (dBm)</th>' +
            '<th>Upper Power Limit (dBm)</th>' +
            '<th>Lower SNR Limit (dB)</th>' +
            '<th>Actual SNR (dB)</th>' +
            '<th>Corrected (Symbols)</th>' +
            '<th>Uncorrected (Symbols)</th>' +
            '</tr>' +
            '<tr>' +
            '<td>' + frequency + '</td>' +
            '<td>' + str(lower_power_limit) + '</td>' +
            '<td' + power_style + '>' + power + '</td>' +
            '<td>' + str(upper_power_limit) + '</td>' +
            '<td>' + str(lower_snr_limit) + '</td>' +
            '<td' + snr_style + '>' + snr + '</td>' +
            '<td>' + corrected + '</td>' +
            '<td>' + uncorrected + '</td>' +
            '</tr>' +
            '</table>' +
            '<h3>Downstream Channel Graphs</h3>' +
            '<img src="downstream_' + frequency + '_power.png"/><br/><br/>' +
            '<img src="downstream_' + frequency + '_snr.png"/><br/><br/>' +
            '<img src="downstream_' + frequency + '_corrected.png"/><br/><br/>' +
            '<img src="downstream_' + frequency + '_uncorrected.png"/>' +
            '</body></html>'
        )

        with open(web_path + 'downstream_' + frequency + '.html', 'w') as f:
            f.write(ch_page_contents)

    # power

    os.system(ds_power_all_cmd)

    # snr

    os.system(ds_snr_all_cmd)

    # corrected

    os.system(ds_corrected_all_cmd)

    # uncorrected

    os.system(ds_uncorrected_all_cmd)

    index_page_ds_summary_contents = index_page_ds_summary_contents + str(
        '</table>'
    )

    # **** UPSTREAM ****

    us_path = db_path + 'data/upstream/'

    index_page_us_summary_contents = str(
        '<h3>Upstream Channels Summary</h3>' +
        '<table border="1"><tr><th>Frequency (Hz)</th><th>Width (Hz)</th><th>Power (dBm)</th></tr>'
    )

    # width

    us_width_all_path = graph_path + 'upstream_all_width' + img_ext

    us_width_all_cmd = str(
        'rrdtool graph ' + us_width_all_path + ' -a PNG ' +
        '--width 800 --height 400 --title "Width" ' +
        '--vertical-label "Hz" --disable-rrdtool-tag '
    )

    # power

    us_power_all_path = graph_path + 'upstream_all_power' + img_ext

    us_power_all_cmd = str(
        'rrdtool graph ' + us_power_all_path + ' -a PNG ' +
        '--width 800 --height 400 --title "Power" ' +
        '--vertical-label "dBm" --disable-rrdtool-tag '
    )

    for us_channel in channels['upstream']:
        channel_count = len(channels['upstream'])

        frequency = us_channel['frequency']
        width = us_channel['width']
        power = us_channel['power']

        us_ch_path = us_path + frequency + db_ext

        if (not os.path.exists(us_ch_path)):
            os.system(
                'rrdtool create ' + us_ch_path + ' ' +
                '--start N --step 300 ' +
                'DS:width:GAUGE:600:U:U ' +
                'DS:power:GAUGE:600:U:U ' +
                'RRA:AVERAGE:0.5:1:1440'
            )

        os.system(
            'rrdtool update ' + us_ch_path + ' ' +
            'N:' + width + ':' + power
        )

        # width

        width_graph_path = graph_path + 'upstream_' + frequency + '_width' + img_ext

        os.system(
            'rrdtool graph ' + width_graph_path + ' -a PNG --title="' + frequency + ' Hz" ' +
            '--vertical-label "Hz" --disable-rrdtool-tag ' +
            'DEF:width=' + us_ch_path + ':width:AVERAGE ' +
            'LINE1:width#ff0000:Width'
        )

        us_width_all_cmd = us_width_all_cmd + str(
            'DEF:' + frequency + '=' + us_ch_path + ':width:AVERAGE ' +
            'LINE1:' + frequency + '#ff0000:' + frequency + 'Hz '
        )

        # power

        power_graph_path = graph_path + 'upstream_' + frequency + '_power' + img_ext

        os.system(
            'rrdtool graph ' + power_graph_path + ' -a PNG --title="' + frequency + ' Hz" ' +
            '--vertical-label "dBm" --disable-rrdtool-tag ' +
            'DEF:power=' + us_ch_path + ':power:AVERAGE ' +
            'LINE1:power#ff0000:Power'
        )

        us_power_all_cmd = us_power_all_cmd + str(
            'DEF:' + frequency + '=' + us_ch_path + ':power:AVERAGE ' +
            'LINE1:' + frequency + '#ff0000:' + frequency + 'Hz '
        )

        # power

        if (channel_count == 1):
            lower_power_limit = 45
            upper_power_limit = 61
        elif (channel_count == 2):
            lower_power_limit = 45
            upper_power_limit = 54
        else:
            lower_power_limit = 45
            upper_power_limit = 51

        if ((float(power) > lower_power_limit) and (float(power) < upper_power_limit)):
            power_style = ' style="background-color:#00FF00"'
        else:
            power_style = ' style="background-color:#FF0000"'

        index_page_us_summary_contents = index_page_us_summary_contents + str(
            '<tr>' +
            '<td><a href="upstream_' + frequency + '.html">' + frequency + '</a></td>' +
            '<td>' + width + '</td>' +
            '<td' + power_style + '>' + power + '</td>' +
            '</tr>'
        )

        ch_page_contents = str(
            '<html><head><title>Upstream Channel Details (' + frequency + ' Hz)</title></head><body>' +
            '<h2>Upstream Channel Details (' + frequency + ' Hz)</h2>' +
            '<h3>Last Update</h3>' +
            '<p>' + datetime.datetime.utcnow().isoformat() + '</p>' +
            '<h3>Upstream Channel Summary</h3>' +
            '<table border="1">' +
            '<tr>' +
            '<th>Frequency (Hz)</th>' +
            '<th>Width (Hz)</th>' +
            '<th>Lower Power Limit (dBm)</th>' +
            '<th>Actual Power (dBm)</th>' +
            '<th>Upper Power Limit (dBm)</th>' +
            '</tr>' +
            '<tr>' +
            '<td>' + frequency + '</td>' +
            '<td>' + width + '</td>' +
            '<td>' + str(lower_power_limit) + '</td>' +
            '<td' + power_style + '>' + power + '</td>' +
            '<td>' + str(upper_power_limit) + '</td>' +
            '</tr>' +
            '</table>' +
            '<h3>Upstream Channel Graphs</h3>' +
            '<img src="upstream_' + frequency + '_width.png"/><br/><br/>' +
            '<img src="upstream_' + frequency + '_power.png"/>' +
            '</body></html>'
        )

        with open(web_path + 'upstream_' + frequency + '.html', 'w') as f:
            f.write(ch_page_contents)

    # width

    os.system(us_width_all_cmd)

    # power

    os.system(us_power_all_cmd)

    index_page_us_summary_contents = index_page_us_summary_contents + str(
        '</table>'
    )

    index_contents = index_contents + str(
        index_page_ds_summary_contents +
        index_page_us_summary_contents +
        '<h3>Downstream Channels Graphs</h3>' +
        '<img src="downstream_all_power.png"/><br/><br/>' +
        '<img src="downstream_all_snr.png"/><br/><br/>' +
        '<img src="downstream_all_corrected.png"/><br/><br/>' +
        '<img src="downstream_all_uncorrected.png"/><br/><br/>' +
        '<h3>Upstream Channels Graphs</h3>' +
        '<img src="upstream_all_width.png"/><br/><br/>' +
        '<img src="upstream_all_power.png"/>' +
        '</body></html>'
    )

    with open(web_path + 'index.html', 'w') as f:
        f.write(index_contents)

# with open('cmconnectionstatus.html') as f:
    # page = f.read()

page = urlopen(cm_status_url).read()

channels = parse_cmstatus(page)

update_rrd(channels)
