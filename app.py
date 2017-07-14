
import dash
import dash_core_components as dcc
import dash_html_components as html
from bs4 import BeautifulSoup
import requests
import pandas as pd
import plotly.graph_objs as go 
from plotly.tools import FigureFactory as FF
from flask import Flask


def createFigure(passback):
    url = 'https://en.wikipedia.org/wiki/The_Bachelorette_(season_13)'
    
    teamDict = {
    'Bryan':['Ben and Erin',1],
    'Peter':['Jessica and Justin',2],
    'Eric':['Beth and Jon',3],
    'Dean':['Meghan and David',4],
    'Josiah':['Natalie and Joseph',5],
    'Will':['Natalie and Joseph',6],
    'Fred':['Meghan and David',7],
    'Jack':['Beth and Jon',8],
    'DeMario':['Jessica and Justin',9],
    'Matt':['Ben and Erin',10],
    'Kenny':['Ben and Erin',11],
    'Anthony':['Jessica and Justin',12],
    'Jamey':['Beth and Jon',13],
    'Lee':['Meghan and David',14],
    'Alex':['Natalie and Joseph',15],
    'Diggy':['Natalie and Joseph',16],
    'Adam':['Meghan and David',17],
    'Bryce':['Beth and Jon',18],
    'Brady':['Jessica and Justin',19],
    'Lucas':['Ben and Erin',20],
    }
    
    teamColors = {
    'Beth and Jon':'rgba(31, 119, 180, 1)',
    'Ben and Erin':'rgba(255, 127, 14, 1)',
    'Natalie and Joseph':'rgba(44, 160, 44, 1)',
    'Jessica and Justin':'rgba(214, 39, 40, 1)',
    'Meghan and David':'rgba(148, 103, 189, 1)'
    }
    
    
    # SCRAPE WIKIPEDIA AND CALCULATE SCORES
    
    r  = requests.get(url)
    wiki = r.text
    
    soup = BeautifulSoup(wiki,'html')
    
    #print soup.prettify()
    
    results=[]
    tableCount=0
    for t in soup.find_all('table'):
        if tableCount == 2:
            for tr in t.find_all('tr'):
                for th in tr.find_all('th'):
                    order = th.text
                if order.isdigit():
                    order = int(order)
                    week = 0
                    for td in tr.find_all('td'):
        #                    print '\n\n\n' + str(week)
        #                    print td.text.split('\n')
                        baches = td.text.split('\n')
                        for i in range(len(baches)):
                            bach = baches[i].split('[')[0]
        #                        bach = td.text.split('[')[0]
        #                    if len(td)>1:
        #                        bach = td.text.split('[')[0]
        #                    else:
        #                        bach = td.string
                            points = 10 + order
                            notes = ''
                            #bach = td.string
                            if bach in teamDict.keys():
                                team = teamDict[bach][0]
                                pick = teamDict[bach][1]
                                if 'bgcolor' in td.attrs and td['bgcolor'] in ['skyblue','gold']:
                                    notes = 'Bonus'
                                    points = points + 10
                                elif 'bgcolor' in td.attrs and td['bgcolor'] in ['limegreen']:
                                    notes = 'Winner'
                                    points = points + 20
                                elif 'bgcolor' in td.attrs:
                                    continue
                                if week <= 1:
                                    points = 0
                                results.append([team,bach,pick,'Week ' + str(week),week,points,notes])
                        week += 1
        tableCount += 1 
    
    resultsDf = pd.DataFrame(results,columns=['Team','Bachelor','Pick','Week','Week Number','Points','Notes']).sort_values(by=['Week Number','Team','Pick'])
    
    #resultsDf[resultsDf['Bachelor'].str.contains('Christen')]
    #resultsDf.to_csv('/Users/JM_JM/Desktop/auto_bachelor_data.csv')
    
    
    
    # CREATE SCOREBOARD TABLE AND PUSH TO PLOTLY
    teamDf = resultsDf[(resultsDf['Week']!='Week 0') & (resultsDf['Week']!='Week 1')].groupby(by=['Team','Week Number']).sum()
    del teamDf['Pick']
    teamDf.reset_index(level=[0,1],inplace=True)
    teamDf = teamDf.pivot(index='Team', columns='Week Number', values='Points').fillna(0)
    teamDf['Total'] = teamDf.sum(axis=1)
    teamDf = teamDf.reset_index().sort_values(by='Total',ascending=False)
    
    if passback=='table':
        table = FF.create_table(teamDf)
        table.layout.width=1000    
#        table.layout.margin=go.Margin(
#                            l=100,
#                            r=100,
#                            b=100,
#                            t=100,
#                            pad=5
#                        )
        #py.iplot(table, filename='Rachel - Overall Ranking')
        return table
    
    data=[]
    bachList = resultsDf['Bachelor'].unique().tolist()
    bachList = sorted(bachList, key=lambda x: teamDict[x][1])
    weekList = resultsDf['Week'].unique().tolist()
    for w in weekList:
        if w not in ['Week 0','Week 1']:
            r = resultsDf[resultsDf['Week']==w]
            y = bachList
            x = []
            for b in bachList:
                if len(r[r['Bachelor']==b]['Points'])==0:
                    x.append(0)
                else:
                    x.append(r[r['Bachelor']==b]['Points'].values[0])
            n = w
            if teamDict[y[0]][1] == 1:
                x.reverse()
                y.reverse()
            trace = go.Bar(
                    y = y,
                    x = x,
                    name = n,
                    orientation = 'h'
                    )
    #        print x
    #        print y
    #        print trace
            data.append(trace)
    
    layout = go.Layout(
        barmode='stack',
        title='Bachelor Performance (in draft order)',
        autosize=False,
        width=960,
        height=800,    
        margin=go.Margin(
                            l=100,
                            r=100,
                            b=100,
                            t=100,
                            pad=5
                        ),
    )
    
    if passback=='horizontalBarChart':
        fig = go.Figure(data=data, layout=layout)
        return fig
    
    bachDf = resultsDf.groupby(by=['Team','Bachelor']).sum()
    del bachDf['Pick']
    bachDf = bachDf.reset_index()
    
    # figure out which week it is so we can blur out bar of eliminated girls
    currentWeek = resultsDf[resultsDf['Notes']!='Bonus'].sort_values(by='Week Number',ascending=False)['Week'].values[0]
    
    
    data=[]
    teamList = resultsDf['Team'].unique().tolist()
    for t in teamList:
        r = resultsDf[resultsDf['Team']==t].groupby(by=['Bachelor']).sum().reset_index()
        x = r['Bachelor'].tolist()
        y = r['Points'].tolist()
        n = t
        # set opacities
        op = []
        for i in range(len(x)):
            if x[i] in resultsDf[resultsDf['Week']==currentWeek]['Bachelor'].tolist():
                op.append(',1)')
            else:
                op.append(',.33)')
        # figure out what bar's legend to show
        sl = []
        for i in range(len(x)):
            if x[i] in resultsDf[resultsDf['Week']==currentWeek]['Bachelor'].tolist() and not(any(sl)):
                sl.append(True)
            elif any(sl):
                sl.append(False)
            elif i == len(x) - 1:
                sl.append(True)
            else:
                sl.append(False)
        #print(y)
        #print(x)
        #print(n)
        for i in range(len(x)):
            trace = go.Bar(
                    y = [y[i]],
                    x = [x[i]],
                    name = n,
                    showlegend = sl[i],
                    marker = dict(
                        color = teamColors[n][:-2] + op[i]
                        )
                    )
            data.append(trace)
    
    layout = go.Layout(
        barmode='group',
        title='Team Performance',
        autosize=False,
        width=960,
        height=800,    
        margin=go.Margin(
                            l=100,
                            r=100,
                            b=100,
                            t=100,
                            pad=5
                        ),
    )

    if passback=='teamGroupedBarChart':
        print(data)
        print(layout)
        fig = go.Figure(data=data, layout=layout)
        return fig
    
md_text ="""
# Fantasy Bachelorette Scoreboard

![Image of Rachel](https://img.buzzfeed.com/buzzfeed-static/static/2017-06/4/11/asset/buzzfeed-prod-fastlane-02/sub-buzz-6780-1496589815-12.jpg?downsize=715:*&output-format=auto&output-quality=auto)

### Here's the new and improved scoreboard app for this season of the Bachelorette!
p.s. it's still in development with more features coming...

"""    
   
 
server=Flask('dash-bachelorette-rachel')
app = dash.Dash('dash-bachelorette-rachel',server=server)

app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})
#app.css.append_css({"external_url": "https://raw.githubusercontent.com/monaldoj/dash-bachelorette-rachel/master/dash-bachelorette.css"})


app.layout = html.Div(children=[

    dcc.Markdown(md_text),

    dcc.Graph(
        id='bTable',
        figure=createFigure('table')
    ),

     dcc.Graph(
        id='bChart2',
        figure=createFigure('teamGroupedBarChart')
    ),
     
    dcc.Graph(
        id='bChart1',
        figure=createFigure('horizontalBarChart')
    ),

])


# Run the Dash app
if __name__ == '__main__':
    app.server.run(debug=True, threaded=True)
    #app.run_server(debug=True)
