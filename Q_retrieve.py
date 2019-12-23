from Qualtrics import set_chosen_data
import lncdSql
import pandas as pd

#Get the name from the database
def get_data(d_qu, task, l_f_name, l_id):

    new_header = d_qu.iloc[0] #grab the first row for the header
    d_qu = d_qu[1:] #take the data less the header row
    d_qu.columns = new_header #set the header row as header
    # print(d_qu.columns)

    # print(d_qu)

    # print(d_qu.RecipientFirstName[2])
    # print('++++++++++++++++++++++')
    #append all the dataframe gotten from Qualtrics to the research list
    # research.append[d_qu]
    # print(l_f_name[0][1])
    # print('+++++++++++++')
    if task == '7TScreening':
        print('------------')
        print(l_f_name[0][0] )
        #Here you go with the row data
        data = d_qu[(d_qu['RecipientFirstName']==l_f_name[0][0]) & (d_qu['RecipientLastName'] == l_f_name[0][1])]

    elif task == '7TBattery':
        data = d_qu[d_qu['ExternalDataReference']==l_id[0][0]]
    #Got the data into database
    print('Data got from the researches')
    print(data)
    # print(d_qu[d_qu['ExternalDataReference']])

    return data


def retrieve_name(vid, task):

    task_list = []
    name_li = ['task', 'sex', 'study', 'age']
    research = []
    name = {}
    #Import the sql first
    sql = lncdSql.lncdSql('config.ini')
    data = sql.query.q_qualtrics(vid = vid, task = task)
    #It's a tuple within a list
    data = data[0]
    # print('-----------')
    # print(data[4])
    # print('-----------')
    l_f_name = sql.query.get_name(pid = data[4])
    l_id = sql.query.get_lunaid_from_pid(pid = data[4])
    # print('-----------')
    # print(l_f_name[0][0], l_f_name[0][1])
    # print('-----------')

    #Suppose that it is a list
    #Only need the task of Battery or Screening
    # Task is the third one
    # for i in data:
    #     if i[2] == '7TBattery' or i[2] == '7TScreening':
    #         #If one person have multiple battery or screening?
    #         task_list.append(i)

    #construct the name using the task_list data
    #Don;t know what time point is so just temporarily set it to zero
    # for j in task_list:
    #name_li and task_list should have the same sequence and the same key
    for i in range(0, len(name_li)):
        name[name_li[i]] = data[i]
    #Now got the name dictionary as name_list
    #Call the Qualtrics retrieving system
    print('++++++++++')
    print(name)
    print('++++++++++')
    d_qu = set_chosen_data(name)

    get_data(d_qu, task, l_f_name, l_id)





# result = retrieve_name(378)

