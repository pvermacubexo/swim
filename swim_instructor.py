from django_seed import Seed

from Appointment.models import Appointment

seeder = Seed.seeder()

from user.models import User
seeder.add_entity(Appointment, 10,
                  {

                  })
seeder.add_entity(User, 5)

inserted_pks = seeder.execute()