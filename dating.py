import dash
import dash_core_components as dcc 
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.graph_objs as go 
import sqlalchemy 
import pymysql
from datetime import datetime, timedelta
import pandas as pd
import dash_table

app=dash.Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB])
server = app.server
##connecting to the DB
conn = pymysql.connect('HOSTNAME',user='USER', password = 'PASSWORD' ,database = 'DBNAME')
cursor = conn.cursor()
cursor = conn.cursor()

## Getting user info with their hobbies
cursor.execute('select a.id as ID, a.name as Name,a.gender as Gender,a.created_on as Date_joined,a.updated_on as Date_updated,a.deleted_on as Date_deleted, c.hobby as Hobby from users a  left join user_hobbies b on a.id=b.user_no  left join interests c on b.hobby_id=c.id')
df1=pd.DataFrame(cursor.fetchall())
df1.rename(columns={0:"ID",1:"Name",2:"Gender",3:"Date_joined",4:"Updated_on",5:"Deleted_on",6:'Hobby'},inplace=True)
df1['Date_joined']=pd.to_datetime(df1['Date_joined']).dt.date
df1['Updated_on']=pd.to_datetime(df1['Updated_on']).dt.date
df1['Deleted_on']=pd.to_datetime(df1['Deleted_on']).dt.date
df1.drop_duplicates(subset=['ID'],inplace=True)#removing duplicate ID's

## Getting user info with their interest/business
cursor = conn.cursor()
cursor.execute( 'select a.id as ID, a.name as Name,c.type as Business from users a left join user_business b on a.id=b.user_no  left join yobusiness c on b.business_no=c.id')
df2=pd.DataFrame(cursor.fetchall())
df2.rename(columns={0:"ID",1:"Name",2:"Business"},inplace=True)
df2.drop_duplicates(subset=['ID'],inplace=True)

##Merging the 2 datasets into one
data = pd.merge(df1,df2)

#finding new users with 24 hours
currentdate=data['Updated_on'].max()
previousdate=data['Updated_on'].max()-timedelta(days=1)

#data for line graph
nowdate=data['Updated_on'].sort_values(ascending=False)
uniquedate=nowdate.unique()
df=[]
for i in uniquedate:
    df.append({'Date': i, 'New_User':'{}'.format(len(data[(data['Updated_on']>i-timedelta(days=1)) & (data['Updated_on']<=i)]))})
df=pd.DataFrame(df)   
df['Date']=pd.to_datetime(df['Date'],format="%Y-%m-%d")
df['New_User']=df['New_User'].astype('int')

##TYpe of jobs
cursor = conn.cursor()
cursor.execute('select job, count(*) as count from profile group by job')
jobdata=pd.DataFrame(cursor.fetchall())
jobdata.rename(columns={0:"Job",1:"Count"},inplace=True)

app.layout=html.Div([
	dbc.Row([
		dbc.Col(html.Div([
			dbc.Card([
				dbc.CardHeader('Active Users'),
				dbc.CardBody(len(data))
				])
			]),width=4),
		dbc.Col(html.Div([
			dbc.Card([
				dbc.CardHeader("New Users"),
				dbc.CardBody(len(data[(data['Updated_on']>previousdate) & (data['Updated_on']<=currentdate)]))
				])
			]),width=4),
		dbc.Col(html.Div([
			dbc.Card([
				dbc.CardHeader("Deleted users"),
				dbc.CardBody(0)])

			]),width=4)
		]),
	dbc.Row([
		dbc.Col(html.Div([
			dcc.Graph(id='gender',
					  figure={
					  		'data':[go.Bar(x=data['Gender'].value_counts().keys().tolist(),y=data['Gender'].value_counts().values.tolist())],
					  		'layout':go.Layout(title='Distribution of Users per Gender',
					  						  xaxis={'title':"Gender"},
					  						  yaxis={'title':'Count'},
					  						  legend={'title':'Gender'},
					  						  hovermode='closest')
					  })
			]),width=6),
		dbc.Col(html.Div([
			dcc.Graph(id='pie graph',
				      figure={
				      		'data':[go.Pie(labels=data['Business'].value_counts().keys().tolist(),values=data['Business'].value_counts().values.tolist())],
				      		'layout':go.Layout(title="Distribution of users' Business",
				      						   legend={'title':'Type of Business'},
				      						   hovermode='closest')
				      })
			]),width=6)


		]),
	dbc.Row([
		dbc.Col(html.Div([
			dcc.Graph(id='line graph',
					  figure={
					  		  'data':[go.Scatter(x=df['Date'],y=df['New_User'],mode='lines')],
					  		  'layout':go.Layout(title='Trend of New Users',
					  		  					 xaxis={'title':'Dates',
					  		  					 		'tickangle': 45},
					  		  					 yaxis={'title':'Number of New users'},
					  		  					 hovermode='closest')
					  }
				)
			]),width=6),

		dbc.Col(html.Div([
			dcc.Graph(id='bar',
					  figure={
					  		  'data':[go.Bar(x=jobdata['Count'],y=jobdata['Job'],orientation='h')],
					  		  'layout':go.Layout(title='Carees for Users ',
					  		  					 xaxis={'title':'Number of users'},
					  		  					 yaxis={'title':'Jobs',
					  		  					 		'tickangle': -45},
					  		  					 legend={'title':'Type of Jobs'},
					  		  					 hovermode='closest')
					  }
				)

			]),width=6)
		]),

	dbc.Row(
		dbc.Col(html.Div([
			dash_table.DataTable(
						            id='users-table',
						            data=data.to_dict('records'),
						            columns=[{'name': i, 'id': i} for i in data.columns],
						            fixed_rows={'headers': True},
						            page_size=20, 
						    		style_table={'height': '400px', 'overflowY': 'auto'})
						    		#style_header={'backgroundColor': 'rgb(30, 30, 30)'},
						           # style_cell={
						           #      'backgroundColor': 'rgb(50, 50, 50)',
						           #      'color': 'white'})

			]),width=12))





	

])

if __name__ == '__main__':
	app.run_server(debug=True)

