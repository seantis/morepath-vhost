import morepath
import webtest


def lchop(text, beginning):
    if text.startswith(beginning):
        return text[len(beginning):]
    return text


class VHMRequest(morepath.Request):

    @morepath.reify
    def x_vhm_host(self):
        return self.headers.get('X_VHM_HOST', '').rstrip('/')

    @morepath.reify
    def x_vhm_root(self):
        return self.headers.get('X_VHM_ROOT', '').rstrip('/')

    def transform(self, url):
        if self.x_vhm_root:
            url = '/' + lchop(url, self.x_vhm_root)

        if self.x_vhm_host:
            url = self.x_vhm_host + url

        return url

    def link(self, *args, **kwargs):
        return self.transform(super(VHMRequest, self).link(*args, **kwargs))


if __name__ == '__main__':

    config = morepath.setup()

    class App(morepath.App):
        testing_config = config
        request_class = VHMRequest

    @App.path(path='/')
    class Root(object):
        pass

    @App.path(path='/blog')
    class Blog(object):
        pass

    @App.view(model=Root)
    def view_root(self, request):
        return request.link(self) + ' - root'

    @App.view(model=Blog)
    def view_blog(self, request):
        return request.link(self) + ' - blog'

    config.commit()

    c = webtest.TestApp(App())

    response = c.get('/')
    assert response.body == b'/ - root'

    response = c.get('/blog')
    assert response.body == b'/blog - blog'

    response = c.get('/', headers={'X_VHM_HOST': 'http://example.org'})
    assert response.body == b'http://example.org/ - root'

    response = c.get('/', headers={'X_VHM_HOST': 'http://example.org/'})
    assert response.body == b'http://example.org/ - root'

    response = c.get('/blog', headers={'X_VHM_HOST': 'http://example.org'})
    assert response.body == b'http://example.org/blog - blog'

    response = c.get('/', headers={'X_VHM_ROOT': '/'})
    assert response.body == b'/ - root'

    response = c.get('/blog', headers={'X_VHM_ROOT': '/blog'})
    assert response.body == b'/ - blog'

    response = c.get('/blog', headers={'X_VHM_ROOT': '/blog/'})
    assert response.body == b'/ - blog'

    response = c.get('/blog', headers={
        'X_VHM_ROOT': '/blog', 'X_VHM_HOST': 'https://blog.example.org/'})
    assert response.body == b'https://blog.example.org/ - blog'

    morepath.run(App())
