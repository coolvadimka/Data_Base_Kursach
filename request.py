from models import Unit, Detail, Session


def set_unit(unit: Unit):
    with Session() as session:
        session.add(unit)
        session.commit()

def set_detail(detail: Detail):
    with Session() as session:
        session.add(detail)
        session.commit()