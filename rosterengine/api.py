# a mock rostering engine, using random allocation

import random

__all__=('do_roster',)

def do_roster(time_slot_plans,employee_users):
    """
    :param time_slot_plans: list
    :param employee_users: list
    :return: list of dicts, each dict has id as key and list as value
    """
    result_list=[]
    for slot_plan in time_slot_plans:
        slot_roster_list = []
        # how many needed?
        number_needed = slot_plan.get_number_of_people()
        for i in range(number_needed):
            index_chosen = random.randint(0,len(employee_users)-1)
            slot_roster_list.append(employee_users[index_chosen])
        result_list.append({slot_plan.id:slot_roster_list})

    return result_list