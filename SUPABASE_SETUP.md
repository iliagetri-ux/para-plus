# «Пара+»: включение защищённой публикации новостей

Публичный ключ в `index.html` предназначен только для браузера. Не добавляйте
в репозиторий `service_role`, database password или personal access token.

## Один раз в Supabase

1. Откройте проект `dmvvezrgaanenwccvhai` → **SQL Editor**.
2. Выполните содержимое
   `supabase/migrations/20261027_admin_news.sql` целиком.
3. В **Authentication → Users** создайте первого пользователя-администратора
   с email и надёжным паролем. Если создаёте пользователя вручную, подтвердите
   его email в панели Supabase.
4. Выполните в SQL Editor, подставив email созданного пользователя:

   ```sql
   insert into public.app_admins (user_id, role)
   select id, 'super_admin'
   from auth.users
   where email = 'admin@example.edu';
   ```

5. Откройте приложение, перейдите во вкладку «Администратор» и войдите этим
   email и паролем. Создайте тестовую новость с изображением, затем проверьте
   ленту в приватном окне без входа.

## Настройки Auth перед публикацией

В текущем проекте включён email-вход и требуется подтверждение email. Так как
учётные записи администраторов создаются только вручную, в **Authentication →
Providers → Email** отключите public sign-ups. В **URL Configuration** укажите
Site URL `https://iliagetri-ux.github.io/para-plus/` и добавьте этот же адрес в
Redirect URLs. Это пригодится для подтверждения email и будущего восстановления
пароля. Не выключайте подтверждение email.

После публикации текущей версии администратор может нажать «Забыли пароль?»
прямо в приложении. Письмо Supabase вернёт его на этот Site URL, где появятся
поля для нового пароля. Если URL не добавлен в Redirect URLs, такая ссылка
может не открыться корректно.

Перед первым публичным релизом также задайте минимальную длину пароля не менее
8 символов и, если тариф позволяет, включите проверку скомпрометированных
паролей и MFA для главного администратора.

## Роли

- `super_admin` — главный администратор; его назначают только в SQL Editor.
  Он может создавать, редактировать и удалять новости, а также удалять
  загруженные изображения.
- `admin` — обычный администратор; может создавать и редактировать новости,
  но не удалять их и не изменять роли.

Клиент не может выдать себе ни одну из ролей: у `app_admins` нет политик
INSERT, UPDATE или DELETE для браузерных пользователей. RLS разрешает запись
в `news` и `storage.objects` только после проверки серверной функции
`public.is_app_admin()`.

Чтобы назначить обычного администратора, сначала создайте пользователя в
Authentication, затем выполните:

```sql
insert into public.app_admins (user_id, role)
select id, 'admin'
from auth.users
where email = 'editor@example.edu'
on conflict (user_id) do update set role = excluded.role;
```

## Проверка после миграции

В SQL Editor можно проверить роли и политики следующими запросами:

```sql
select u.email, a.role, a.created_at
from public.app_admins a
join auth.users u on u.id = a.user_id;

select tablename, policyname, roles, cmd
from pg_policies
where (schemaname = 'public' and tablename in ('news', 'app_admins'))
   or (schemaname = 'storage' and tablename = 'objects');
```

Из браузера нельзя надёжно получить список RLS-политик или выполнить SQL
миграцию: для этого потребовался бы секретный ключ. Поэтому этот файл нужно
выполнить владельцу проекта в Supabase Dashboard.
