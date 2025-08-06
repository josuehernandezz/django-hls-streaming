from django import forms

style = "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5  dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"

# Login user in
class SignIn(forms.Form):
    username = forms.CharField(label='Username', max_length=150, required=True, widget=forms.TextInput(attrs={
        'placeholder': 'username',
        'class': style,
    }))
    # password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    password = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={
        'placeholder': '••••••••',
        'class': style
    }))

    class Meta:
        fields = ('username', 'password')
