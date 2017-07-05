import datetime

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, \
    BaseUserManager
from django.core.urlresolvers import reverse
from django.db import transaction
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _, ugettext as __
from lazyutils import delegate_to, lazy

from codeschool import models

strptime = datetime.datetime.strptime


class UserManager(BaseUserManager):

    def _create_user(self, email, name, alias, role, school_id, password, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(name=name, email=email, alias=alias, school_id=school_id,
                          role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, name, alias, role, school_id, password, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, name, alias, role, school_id, password, **extra_fields)

    def create_superuser(self, email, name, alias, role, school_id, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, name, alias, role, school_id, password, **extra_fields)



class User(AbstractBaseUser, PermissionsMixin):
    """
    Base user model.
    """

    REQUIRED_FIELDS = ['alias', 'name', 'school_id', 'role']
    USERNAME_FIELD = 'email'
    ROLE_STUDENT, ROLE_TEACHER, ROLE_STAFF, ROLE_ADMIN = range(4)
    ROLE_CHOICES = enumerate([
        _('Student'), _('Teacher'), _('School staff'), _('Administrator')]
    )

    email = models.EmailField(
        _('E-mail'),
        db_index=True,
        unique=True,
        help_text=_(
            'Users can register additional e-mail addresses. This is the '
            'main e-mail address which is used for login.'
        )
    )
    name = models.CharField(
        _('Name'),
        max_length=140,
        help_text=_(
            'Full name of the user.'
        )
    )
    alias = models.CharField(
        _('Alias'),
        max_length=20,
        help_text=_(
            'Public alias used to identify the user.'
        )
    )
    school_id = models.CharField(
        _('School id'),
        max_length=20,
        blank=False,
        unique=True,
        validators=[],  # TODO: validate school id number
        help_text=_(
            'Identification number in your school issued id card.'
        )
    )
    role = models.IntegerField(
        _('Role'),
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT,
        help_text=_(
            'User main role in the codeschool platform.'
        )
    )
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_(
            'Designates whether the user can log into this admin site.'
        ),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(
        _('date joined'),
        default=timezone.now
    )

    objects = UserManager()

    # Temporary properties defined for compatibility
    username = property(lambda x: x.alias)

    @property
    def profile(self):
        if self.id is None:
            return self._lazy_profile

        try:
            return self.profile_ref
        except AttributeError:
            self.profile_ref = Profile(user=self)
            return self.profile_ref

    @lazy
    def _lazy_profile(self):
        return Profile(user=self)

    def save(self, *args, **kwargs):
        new = self.id is None

        if new:
            with transaction.atomic():
                super().save(*args, **kwargs)
                self.profile.save()
        else:
            super().save(*args, **kwargs)

    def get_full_name(self):
        return self.name.strip()

    def get_short_name(self):
        return self.alias

    def get_absolute_url(self):
        return reverse('users:profile-detail', args=(self.id,))


class ExtraEmail(models.Model):
    """
    Extra e-mails assigned to a Codeschool account.
    """

    user = models.ForeignKey(User)
    email = models.EmailField(unique=True)


class Profile(models.TimeStampedModel):
    """
    Social information about users.
    """

    GENDER_MALE, GENDER_FEMALE, GENDER_OTHER = 0, 1, 2
    GENDER_CHOICES = [
        (GENDER_MALE, _('Male')),
        (GENDER_FEMALE, _('Female')),
        (GENDER_OTHER, _('Other')),
    ]

    VISIBILITY_PUBLIC, VISIBILITY_FRIENDS, VISIBILITY_HIDDEN = range(3)
    VISIBILITY_CHOICES = enumerate(
        [_('Any Codeschool user'), _('Only friends'), _('Private')]
    )

    visibility = models.IntegerField(
        _('Visibility'),
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_FRIENDS,
        help_text=_(
            'Who do you want to share information in your profile?'
        )
    )
    user = models.OneToOneField(
        User,
        verbose_name=_('user'),
        related_name='profile_ref',
    )
    phone = models.CharField(
        _('Phone'),
        max_length=20,
        blank=True,
        null=True,
    )
    gender = models.SmallIntegerField(
        _('gender'),
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
    )
    date_of_birth = models.DateField(
        _('date of birth'),
        blank=True,
        null=True,
    )
    website = models.URLField(
        _('Website'),
        blank=True,
        null=True,
        help_text=_(
            'A website that is shown publicly in your profile.'
        )
    )
    about_me = models.RichTextField(
        _('About me'),
        blank=True,
        help_text=_(
            'A small description about yourself.'
        )
    )

    # Delegates and properties
    username = delegate_to('user', True)
    name = delegate_to('user')
    email = delegate_to('user')

    class Meta:
        permissions = (
            ('student', _('Can access/modify data visible to student\'s')),
            ('teacher', _('Can access/modify data visible only to Teacher\'s')),
        )

    @property
    def age(self):
        if self.date_of_birth is None:
            return None
        today = timezone.now().date()
        birthday = self.date_of_birth
        years = today.year - birthday.year
        birthday = datetime.date(today.year, birthday.month, birthday.day)
        if birthday > today:
            return years - 1
        else:
            return years

    def __str__(self):
        if self.user is None:
            return __('Unbound profile')
        full_name = self.user.get_full_name() or self.user.username
        return __('%(name)s\'s profile') % {'name': full_name}

    def get_absolute_url(self):
        self.user.get_absolute_url()
