.PHONY: test version

prepare_test_env:
	pip install -e .
	pip install -r requirements-test.txt
	docker run -d -p 2222:22 -v `pwd`/examples:/examples -v `pwd`/test/id_rsa.pub:/root/.ssh/authorized_keys  docker.io/panubo/sshd
	sleep 1
	touch prepare_test_env

test: prepare_test_env
	py.test -s --cov paramiko_expect --cov-report term-missing

version:
	set -x
	set -e
	
	git fetch
	git checkout master
	git rebase upstream/master
	read -p "tag: " TAG
	python -c "import packaging.version ; print packaging.version.Version('$TAG')"
	sed "s/version=.*,/version='$TAG',/" setup.py -i
	git add setup.py
	git commit -m "version $TAG"
	git tag $TAG
	git push upstream master --tags
		
