from django.core.mail import send_mail
from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers


User = get_user_model()


class RegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6)
    password_confirmation = serializers.CharField(min_length=6)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)

    def validate_email(self, email):
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email уже занят")
        return email

    def validate(self, data):
        password1 = data.get("password")
        password2 = data.pop("password_confirmation")
        if password1 != password2:
            raise serializers.ValidationError("Пароли не совпадают")
        return data

    def _send_activation_mail(self, email, code):
        message = f"""
                    Благодарим Вас за регистрацию на нашем сайте.
                    Ваш код активации: {code}
                    """
        send_mail(
            'Активация аккаунта',
            message,
            'test@gmail.com',
            [email]
        )

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.generate_activation_code()
        self._send_activation_mail(user.email, user.activation_code)
        return user


class ActivationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)

    def validate(self, attrs):
        email = attrs.get('email')
        code = attrs.get('code')
        if not User.objects.filter(email=email, activation_code=code).exists():
            raise serializers.ValidationError("Пользователь не найден")
        return attrs

    def activate(self, data):
        email = data.get('email')
        code = data.get('code')
        user = User.objects.get(email=email)
        user.is_active = True
        user.activation_code = ""
        user.save()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate_email(self, email):
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Пользователь не зарегистрирован")
        return email

    def validate(self, data):
        request = self.context.get('request')
        email = data.get('email')
        password = data.get('password')
        if email and password:
            user = authenticate(username=email,
                                password=password,
                                request=request)
            if not user:
                raise serializers.ValidationError('Неверный email или пароль')
        else:
            raise serializers.ValidationError('Email и пароль обязательны')
        data['user'] = user
        return data